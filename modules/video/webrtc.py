"""
NEXUS WebRTC Module - WebRTC Signaling and Peer Connection Management
Handles WebRTC peer connections, signaling, ICE, and media streams
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Callable, Any
from uuid import uuid4
import asyncio
import json
import logging

logger = logging.getLogger(__name__)


class SignalingState(Enum):
    """WebRTC signaling states"""
    STABLE = "stable"
    HAVE_LOCAL_OFFER = "have-local-offer"
    HAVE_REMOTE_OFFER = "have-remote-offer"
    HAVE_LOCAL_PRANSWER = "have-local-pranswer"
    HAVE_REMOTE_PRANSWER = "have-remote-pranswer"
    CLOSED = "closed"


class IceConnectionState(Enum):
    """ICE connection states"""
    NEW = "new"
    CHECKING = "checking"
    CONNECTED = "connected"
    COMPLETED = "completed"
    FAILED = "failed"
    DISCONNECTED = "disconnected"
    CLOSED = "closed"


class IceGatheringState(Enum):
    """ICE gathering states"""
    NEW = "new"
    GATHERING = "gathering"
    COMPLETE = "complete"


class PeerConnectionState(Enum):
    """Overall peer connection states"""
    NEW = "new"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    FAILED = "failed"
    CLOSED = "closed"


@dataclass
class IceCandidate:
    """Represents an ICE candidate"""
    candidate: str
    sdp_mid: str
    sdp_m_line_index: int
    username_fragment: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "candidate": self.candidate,
            "sdpMid": self.sdp_mid,
            "sdpMLineIndex": self.sdp_m_line_index,
            "usernameFragment": self.username_fragment,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'IceCandidate':
        """Create from dictionary"""
        return cls(
            candidate=data.get("candidate", ""),
            sdp_mid=data.get("sdpMid", ""),
            sdp_m_line_index=data.get("sdpMLineIndex", 0),
            username_fragment=data.get("usernameFragment"),
        )


@dataclass
class SessionDescription:
    """Represents SDP session description"""
    type: str  # "offer" or "answer"
    sdp: str

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "type": self.type,
            "sdp": self.sdp,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'SessionDescription':
        """Create from dictionary"""
        return cls(
            type=data.get("type", ""),
            sdp=data.get("sdp", ""),
        )


@dataclass
class MediaStreamConstraints:
    """Media stream constraints for getUserMedia"""
    video: bool = True
    audio: bool = True
    video_constraints: Dict = field(default_factory=lambda: {
        "width": {"ideal": 1920},
        "height": {"ideal": 1080},
        "frameRate": {"ideal": 30},
        "facingMode": "user",
    })
    audio_constraints: Dict = field(default_factory=lambda: {
        "echoCancellation": True,
        "noiseSuppression": True,
        "autoGainControl": True,
    })

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        video_config = self.video_constraints if self.video else False
        audio_config = self.audio_constraints if self.audio else False

        return {
            "video": video_config,
            "audio": audio_config,
        }


@dataclass
class PeerConnectionConfig:
    """Configuration for RTCPeerConnection"""
    ice_servers: List[Dict] = field(default_factory=lambda: [
        {"urls": "stun:stun.l.google.com:19302"},
        {"urls": "stun:stun1.l.google.com:19302"},
        {"urls": "stun:stun2.l.google.com:19302"},
    ])
    ice_transport_policy: str = "all"  # "all" or "relay"
    bundle_policy: str = "balanced"  # "balanced", "max-compat", or "max-bundle"
    rtcp_mux_policy: str = "require"  # "negotiate" or "require"
    sdp_semantics: str = "unified-plan"  # "plan-b" or "unified-plan"
    enable_dtls_srtp: bool = True

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "iceServers": self.ice_servers,
            "iceTransportPolicy": self.ice_transport_policy,
            "bundlePolicy": self.bundle_policy,
            "rtcpMuxPolicy": self.rtcp_mux_policy,
            "sdpSemantics": self.sdp_semantics,
        }


class MediaStream:
    """Represents a media stream with tracks"""

    def __init__(self, stream_id: Optional[str] = None):
        self.id = stream_id or str(uuid4())
        self.audio_tracks: List[Dict] = []
        self.video_tracks: List[Dict] = []
        self.active = True

    def add_audio_track(self, track: Dict) -> None:
        """Add an audio track"""
        self.audio_tracks.append(track)

    def add_video_track(self, track: Dict) -> None:
        """Add a video track"""
        self.video_tracks.append(track)

    def get_tracks(self) -> List[Dict]:
        """Get all tracks"""
        return self.audio_tracks + self.video_tracks

    def stop(self) -> None:
        """Stop all tracks in the stream"""
        self.active = False
        for track in self.get_tracks():
            track["enabled"] = False


class PeerConnection:
    """
    Represents a WebRTC peer connection
    Manages SDP negotiation, ICE candidates, and media streams
    """

    def __init__(
        self,
        peer_id: str,
        config: Optional[PeerConnectionConfig] = None,
        is_initiator: bool = False,
    ):
        self.peer_id = peer_id
        self.config = config or PeerConnectionConfig()
        self.is_initiator = is_initiator

        # Connection state
        self.signaling_state = SignalingState.STABLE
        self.ice_connection_state = IceConnectionState.NEW
        self.ice_gathering_state = IceGatheringState.NEW
        self.connection_state = PeerConnectionState.NEW

        # SDP and ICE
        self.local_description: Optional[SessionDescription] = None
        self.remote_description: Optional[SessionDescription] = None
        self.local_candidates: List[IceCandidate] = []
        self.remote_candidates: List[IceCandidate] = []

        # Media streams
        self.local_streams: Dict[str, MediaStream] = {}
        self.remote_streams: Dict[str, MediaStream] = {}

        # Data channels
        self.data_channels: Dict[str, Any] = {}

        # Statistics
        self.bytes_sent = 0
        self.bytes_received = 0
        self.packets_sent = 0
        self.packets_received = 0
        self.created_at = datetime.now()

        # Event handlers
        self.event_handlers: Dict[str, List[Callable]] = {
            "icecandidate": [],
            "icegatheringstatechange": [],
            "iceconnectionstatechange": [],
            "connectionstatechange": [],
            "signalingstatechange": [],
            "track": [],
            "datachannel": [],
            "negotiationneeded": [],
        }

        logger.info(f"PeerConnection created: {peer_id}")

    async def create_offer(self) -> SessionDescription:
        """Create an SDP offer"""
        logger.info(f"Creating offer for peer: {self.peer_id}")

        # Simulate SDP offer creation
        sdp = self._generate_sdp_offer()

        self.local_description = SessionDescription(type="offer", sdp=sdp)
        self.signaling_state = SignalingState.HAVE_LOCAL_OFFER
        self._trigger_event("signalingstatechange", {"state": self.signaling_state})

        return self.local_description

    async def create_answer(self) -> SessionDescription:
        """Create an SDP answer"""
        logger.info(f"Creating answer for peer: {self.peer_id}")

        if not self.remote_description:
            raise ValueError("Cannot create answer without remote description")

        # Simulate SDP answer creation
        sdp = self._generate_sdp_answer()

        self.local_description = SessionDescription(type="answer", sdp=sdp)
        self.signaling_state = SignalingState.STABLE
        self._trigger_event("signalingstatechange", {"state": self.signaling_state})

        return self.local_description

    async def set_local_description(self, description: SessionDescription) -> None:
        """Set the local session description"""
        logger.info(f"Setting local description for peer: {self.peer_id}")
        self.local_description = description

        if description.type == "offer":
            self.signaling_state = SignalingState.HAVE_LOCAL_OFFER
        elif description.type == "answer":
            self.signaling_state = SignalingState.STABLE

        self._trigger_event("signalingstatechange", {"state": self.signaling_state})

    async def set_remote_description(self, description: SessionDescription) -> None:
        """Set the remote session description"""
        logger.info(f"Setting remote description for peer: {self.peer_id}")
        self.remote_description = description

        if description.type == "offer":
            self.signaling_state = SignalingState.HAVE_REMOTE_OFFER
        elif description.type == "answer":
            self.signaling_state = SignalingState.STABLE

        self._trigger_event("signalingstatechange", {"state": self.signaling_state})

    async def add_ice_candidate(self, candidate: IceCandidate) -> None:
        """Add an ICE candidate"""
        logger.debug(f"Adding ICE candidate for peer: {self.peer_id}")
        self.remote_candidates.append(candidate)

    def add_stream(self, stream: MediaStream) -> None:
        """Add a local media stream"""
        logger.info(f"Adding stream {stream.id} to peer: {self.peer_id}")
        self.local_streams[stream.id] = stream
        self._trigger_negotiation_needed()

    def remove_stream(self, stream_id: str) -> bool:
        """Remove a local media stream"""
        if stream_id in self.local_streams:
            del self.local_streams[stream_id]
            logger.info(f"Removed stream {stream_id} from peer: {self.peer_id}")
            self._trigger_negotiation_needed()
            return True
        return False

    def create_data_channel(
        self,
        label: str,
        options: Optional[Dict] = None,
    ) -> str:
        """Create a data channel"""
        channel_id = str(uuid4())
        self.data_channels[channel_id] = {
            "id": channel_id,
            "label": label,
            "options": options or {},
            "readyState": "connecting",
        }
        logger.info(f"Data channel created: {label}")
        return channel_id

    def send_data(self, channel_id: str, data: Any) -> bool:
        """Send data through a data channel"""
        if channel_id not in self.data_channels:
            return False

        channel = self.data_channels[channel_id]
        if channel["readyState"] != "open":
            return False

        # Simulate sending data
        logger.debug(f"Sending data on channel {channel['label']}: {len(str(data))} bytes")
        self.bytes_sent += len(str(data))
        return True

    async def get_stats(self) -> Dict:
        """Get connection statistics"""
        return {
            "peer_id": self.peer_id,
            "signaling_state": self.signaling_state.value,
            "ice_connection_state": self.ice_connection_state.value,
            "ice_gathering_state": self.ice_gathering_state.value,
            "connection_state": self.connection_state.value,
            "bytes_sent": self.bytes_sent,
            "bytes_received": self.bytes_received,
            "packets_sent": self.packets_sent,
            "packets_received": self.packets_received,
            "local_candidates": len(self.local_candidates),
            "remote_candidates": len(self.remote_candidates),
            "local_streams": len(self.local_streams),
            "remote_streams": len(self.remote_streams),
            "data_channels": len(self.data_channels),
        }

    def close(self) -> None:
        """Close the peer connection"""
        logger.info(f"Closing peer connection: {self.peer_id}")

        # Stop all local streams
        for stream in self.local_streams.values():
            stream.stop()

        # Close all data channels
        for channel in self.data_channels.values():
            channel["readyState"] = "closed"

        self.signaling_state = SignalingState.CLOSED
        self.connection_state = PeerConnectionState.CLOSED
        self.ice_connection_state = IceConnectionState.CLOSED

        self._trigger_event("connectionstatechange", {"state": self.connection_state})

    def on_event(self, event_name: str, callback: Callable) -> None:
        """Register an event handler"""
        if event_name in self.event_handlers:
            self.event_handlers[event_name].append(callback)

    def _trigger_event(self, event_name: str, data: Dict) -> None:
        """Trigger an event"""
        if event_name in self.event_handlers:
            for callback in self.event_handlers[event_name]:
                try:
                    callback(data)
                except Exception as e:
                    logger.error(f"Error in event handler {event_name}: {e}")

    def _trigger_negotiation_needed(self) -> None:
        """Trigger negotiation needed event"""
        self._trigger_event("negotiationneeded", {"peer_id": self.peer_id})

    def _generate_sdp_offer(self) -> str:
        """Generate a mock SDP offer"""
        return f"""v=0
o=- {uuid4().int} 2 IN IP4 127.0.0.1
s=-
t=0 0
a=group:BUNDLE 0 1
a=msid-semantic: WMS {uuid4()}
m=audio 9 UDP/TLS/RTP/SAVPF 111 103 104 9 0 8 106 105 13 110 112 113 126
c=IN IP4 0.0.0.0
a=rtcp:9 IN IP4 0.0.0.0
a=ice-ufrag:{uuid4().hex[:8]}
a=ice-pwd:{uuid4().hex}
a=ice-options:trickle
a=fingerprint:sha-256 {':'.join(f'{i:02X}' for i in range(32))}
a=setup:actpass
a=mid:0
a=sendrecv
a=rtcp-mux
m=video 9 UDP/TLS/RTP/SAVPF 96 97 98 99 100 101 102
c=IN IP4 0.0.0.0
a=rtcp:9 IN IP4 0.0.0.0
a=ice-ufrag:{uuid4().hex[:8]}
a=ice-pwd:{uuid4().hex}
a=ice-options:trickle
a=fingerprint:sha-256 {':'.join(f'{i:02X}' for i in range(32))}
a=setup:actpass
a=mid:1
a=sendrecv
a=rtcp-mux
"""

    def _generate_sdp_answer(self) -> str:
        """Generate a mock SDP answer"""
        if not self.remote_description:
            return ""

        # In a real implementation, this would be based on the offer
        return self._generate_sdp_offer().replace("actpass", "active")


class SignalingServer:
    """
    WebRTC signaling server
    Handles signaling between peers for establishing connections
    """

    def __init__(self):
        self.rooms: Dict[str, Set[str]] = {}
        self.peer_connections: Dict[str, PeerConnection] = {}
        self.signaling_queue: asyncio.Queue = asyncio.Queue()
        logger.info("SignalingServer initialized")

    async def join_room(self, room_id: str, peer_id: str) -> None:
        """Add a peer to a room"""
        if room_id not in self.rooms:
            self.rooms[room_id] = set()

        self.rooms[room_id].add(peer_id)
        logger.info(f"Peer {peer_id} joined room {room_id}")

        # Notify other peers
        await self._broadcast_to_room(
            room_id,
            peer_id,
            {
                "type": "peer-joined",
                "peer_id": peer_id,
            }
        )

    async def leave_room(self, room_id: str, peer_id: str) -> None:
        """Remove a peer from a room"""
        if room_id in self.rooms:
            self.rooms[room_id].discard(peer_id)
            logger.info(f"Peer {peer_id} left room {room_id}")

            # Notify other peers
            await self._broadcast_to_room(
                room_id,
                peer_id,
                {
                    "type": "peer-left",
                    "peer_id": peer_id,
                }
            )

    async def send_signal(
        self,
        from_peer: str,
        to_peer: str,
        signal_type: str,
        data: Dict,
    ) -> None:
        """Send a signal from one peer to another"""
        message = {
            "type": signal_type,
            "from": from_peer,
            "to": to_peer,
            "data": data,
            "timestamp": datetime.now().isoformat(),
        }

        await self.signaling_queue.put(message)
        logger.debug(f"Signal sent: {signal_type} from {from_peer} to {to_peer}")

    async def broadcast_to_room(
        self,
        room_id: str,
        from_peer: str,
        signal_type: str,
        data: Dict,
    ) -> None:
        """Broadcast a signal to all peers in a room"""
        await self._broadcast_to_room(room_id, from_peer, {
            "type": signal_type,
            "data": data,
        })

    async def _broadcast_to_room(
        self,
        room_id: str,
        exclude_peer: str,
        message: Dict,
    ) -> None:
        """Internal broadcast method"""
        if room_id not in self.rooms:
            return

        for peer_id in self.rooms[room_id]:
            if peer_id != exclude_peer:
                full_message = {
                    **message,
                    "from": exclude_peer,
                    "to": peer_id,
                    "timestamp": datetime.now().isoformat(),
                }
                await self.signaling_queue.put(full_message)

    def get_room_peers(self, room_id: str) -> List[str]:
        """Get all peers in a room"""
        return list(self.rooms.get(room_id, set()))

    async def process_signaling_messages(self, callback: Callable) -> None:
        """Process signaling messages in the queue"""
        while True:
            message = await self.signaling_queue.get()
            try:
                await callback(message)
            except Exception as e:
                logger.error(f"Error processing signaling message: {e}")


class WebRTCManager:
    """
    High-level WebRTC manager
    Manages peer connections and signaling for a conference
    """

    def __init__(self, conference_id: str):
        self.conference_id = conference_id
        self.peer_connections: Dict[str, PeerConnection] = {}
        self.signaling_server = SignalingServer()
        self.config = PeerConnectionConfig()
        logger.info(f"WebRTCManager initialized for conference: {conference_id}")

    async def add_peer(self, peer_id: str) -> PeerConnection:
        """Add a new peer to the conference"""
        if peer_id in self.peer_connections:
            return self.peer_connections[peer_id]

        pc = PeerConnection(peer_id=peer_id, config=self.config)
        self.peer_connections[peer_id] = pc

        # Join the conference room
        await self.signaling_server.join_room(self.conference_id, peer_id)

        logger.info(f"Peer added: {peer_id}")
        return pc

    async def remove_peer(self, peer_id: str) -> bool:
        """Remove a peer from the conference"""
        if peer_id not in self.peer_connections:
            return False

        pc = self.peer_connections[peer_id]
        pc.close()
        del self.peer_connections[peer_id]

        await self.signaling_server.leave_room(self.conference_id, peer_id)

        logger.info(f"Peer removed: {peer_id}")
        return True

    def get_peer(self, peer_id: str) -> Optional[PeerConnection]:
        """Get a peer connection"""
        return self.peer_connections.get(peer_id)

    def get_all_peers(self) -> List[str]:
        """Get all peer IDs"""
        return list(self.peer_connections.keys())

    async def negotiate_connection(
        self,
        peer1_id: str,
        peer2_id: str,
    ) -> bool:
        """Negotiate a connection between two peers"""
        peer1 = self.get_peer(peer1_id)
        peer2 = self.get_peer(peer2_id)

        if not peer1 or not peer2:
            return False

        try:
            # Peer1 creates offer
            offer = await peer1.create_offer()
            await peer1.set_local_description(offer)

            # Send offer to peer2
            await self.signaling_server.send_signal(
                peer1_id,
                peer2_id,
                "offer",
                offer.to_dict(),
            )

            # Peer2 sets remote description and creates answer
            await peer2.set_remote_description(offer)
            answer = await peer2.create_answer()
            await peer2.set_local_description(answer)

            # Send answer back to peer1
            await self.signaling_server.send_signal(
                peer2_id,
                peer1_id,
                "answer",
                answer.to_dict(),
            )

            # Peer1 sets remote description
            await peer1.set_remote_description(answer)

            logger.info(f"Connection negotiated between {peer1_id} and {peer2_id}")
            return True

        except Exception as e:
            logger.error(f"Error negotiating connection: {e}")
            return False

    async def get_conference_stats(self) -> Dict:
        """Get statistics for all peer connections"""
        stats = {}
        for peer_id, pc in self.peer_connections.items():
            stats[peer_id] = await pc.get_stats()

        return {
            "conference_id": self.conference_id,
            "peer_count": len(self.peer_connections),
            "peers": stats,
        }
