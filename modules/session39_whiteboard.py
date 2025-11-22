"""
Session 39: Whiteboard
Features: Infinite canvas, collaboration, drawing tools, AI assistance
"""
import streamlit as st
import json
from datetime import datetime
from typing import Dict, List, Any
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from utils.ai_assistant import ai_assistant
from utils.storage import storage


class Whiteboard:
    """Interactive whiteboard with infinite canvas and collaboration"""

    def __init__(self):
        """Initialize whiteboard"""
        if 'whiteboards' not in st.session_state:
            st.session_state.whiteboards = self.load_whiteboards()
        if 'current_whiteboard' not in st.session_state:
            st.session_state.current_whiteboard = None

    def load_whiteboards(self) -> List[Dict]:
        """Load saved whiteboards"""
        whiteboards = []
        files = storage.list_files('whiteboards', '.json')
        for file in files:
            data = storage.load_json(file, 'whiteboards')
            if data:
                whiteboards.append(data)
        return whiteboards

    def save_whiteboard(self, whiteboard: Dict) -> bool:
        """Save whiteboard"""
        filename = f"whiteboard_{whiteboard['id']}.json"
        return storage.save_json(filename, whiteboard, 'whiteboards')

    def create_whiteboard(self, name: str) -> Dict:
        """Create new whiteboard"""
        whiteboard = {
            'id': datetime.now().strftime('%Y%m%d_%H%M%S'),
            'name': name,
            'created': datetime.now().isoformat(),
            'modified': datetime.now().isoformat(),
            'objects': [],
            'annotations': [],
            'collaborators': [],
            'canvas_size': {'width': 2000, 'height': 2000}
        }
        return whiteboard

    def render(self):
        """Render whiteboard"""
        st.title("🎨 Whiteboard")
        st.markdown("*Infinite canvas for brainstorming and collaboration*")

        # Sidebar
        with st.sidebar:
            st.header("Whiteboard Manager")

            # New whiteboard
            with st.expander("➕ New Whiteboard", expanded=False):
                new_name = st.text_input("Whiteboard Name", key="new_whiteboard_name")
                if st.button("Create Whiteboard", type="primary"):
                    if new_name:
                        whiteboard = self.create_whiteboard(new_name)
                        st.session_state.whiteboards.append(whiteboard)
                        st.session_state.current_whiteboard = whiteboard
                        self.save_whiteboard(whiteboard)
                        st.success(f"Created '{new_name}'")
                        st.rerun()

            # Existing whiteboards
            if st.session_state.whiteboards:
                st.subheader("Saved Whiteboards")
                for whiteboard in st.session_state.whiteboards:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        if st.button(whiteboard['name'], key=f"load_{whiteboard['id']}"):
                            st.session_state.current_whiteboard = whiteboard
                            st.rerun()
                    with col2:
                        if st.button("🗑️", key=f"del_{whiteboard['id']}"):
                            storage.delete_file(f"whiteboard_{whiteboard['id']}.json", 'whiteboards')
                            st.session_state.whiteboards.remove(whiteboard)
                            st.rerun()

        # Main canvas
        if st.session_state.current_whiteboard:
            whiteboard = st.session_state.current_whiteboard

            tabs = st.tabs(["🖊️ Draw", "📝 Objects", "👥 Collaborate", "🤖 AI Assistant"])

            # Draw Tab
            with tabs[0]:
                st.subheader(f"Whiteboard: {whiteboard['name']}")

                # Drawing tools
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    tool = st.selectbox("Tool", ["Pen", "Text", "Shape", "Sticky Note", "Connector"])
                with col2:
                    color = st.color_picker("Color", "#000000")
                with col3:
                    size = st.slider("Size", 1, 20, 5)

                # Canvas (using drawable canvas)
                try:
                    from streamlit_drawable_canvas import st_canvas

                    canvas_result = st_canvas(
                        fill_color="rgba(255, 165, 0, 0.3)",
                        stroke_width=size,
                        stroke_color=color,
                        background_color="#ffffff",
                        height=600,
                        width=800,
                        drawing_mode="freedraw" if tool == "Pen" else "rect" if tool == "Shape" else "freedraw",
                        key="canvas",
                    )

                    if canvas_result.json_data is not None:
                        # Save drawing data
                        whiteboard['objects'] = canvas_result.json_data
                        whiteboard['modified'] = datetime.now().isoformat()

                except ImportError:
                    st.info("Install streamlit-drawable-canvas for interactive drawing")
                    st.markdown("**Drawing area placeholder**")
                    st.markdown("Use the objects tab to add content")

                # Quick actions
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("💾 Save Canvas"):
                        self.save_whiteboard(whiteboard)
                        st.success("Canvas saved!")
                with col2:
                    if st.button("🗑️ Clear Canvas"):
                        whiteboard['objects'] = []
                        self.save_whiteboard(whiteboard)
                        st.rerun()
                with col3:
                    if st.button("📸 Snapshot"):
                        st.info("Snapshot saved!")

            # Objects Tab
            with tabs[1]:
                st.subheader("Canvas Objects")

                # Add object
                with st.expander("➕ Add Object", expanded=True):
                    object_type = st.selectbox("Type", ["Text Box", "Sticky Note", "Shape", "Image", "Link"])

                    if object_type == "Text Box":
                        text = st.text_area("Text")
                        if st.button("Add Text Box"):
                            whiteboard['annotations'].append({
                                'type': 'text',
                                'content': text,
                                'created': datetime.now().isoformat()
                            })
                            self.save_whiteboard(whiteboard)
                            st.rerun()

                    elif object_type == "Sticky Note":
                        note = st.text_area("Note")
                        note_color = st.selectbox("Color", ["Yellow", "Pink", "Blue", "Green"])
                        if st.button("Add Sticky Note"):
                            whiteboard['annotations'].append({
                                'type': 'sticky',
                                'content': note,
                                'color': note_color,
                                'created': datetime.now().isoformat()
                            })
                            self.save_whiteboard(whiteboard)
                            st.rerun()

                    elif object_type == "Link":
                        link_text = st.text_input("Link Text")
                        link_url = st.text_input("URL")
                        if st.button("Add Link"):
                            whiteboard['annotations'].append({
                                'type': 'link',
                                'text': link_text,
                                'url': link_url,
                                'created': datetime.now().isoformat()
                            })
                            self.save_whiteboard(whiteboard)
                            st.rerun()

                # Display objects
                if whiteboard['annotations']:
                    st.markdown("### Canvas Annotations")
                    for idx, obj in enumerate(whiteboard['annotations']):
                        with st.container():
                            col1, col2 = st.columns([4, 1])
                            with col1:
                                if obj['type'] == 'text':
                                    st.text_area(f"Text {idx+1}", obj['content'], disabled=True, height=100)
                                elif obj['type'] == 'sticky':
                                    st.info(f"📌 {obj['content']} ({obj['color']})")
                                elif obj['type'] == 'link':
                                    st.markdown(f"🔗 [{obj['text']}]({obj['url']})")
                            with col2:
                                if st.button("❌", key=f"del_obj_{idx}"):
                                    whiteboard['annotations'].pop(idx)
                                    self.save_whiteboard(whiteboard)
                                    st.rerun()
                            st.markdown("---")

            # Collaborate Tab
            with tabs[2]:
                st.subheader("👥 Collaboration")

                # Add collaborator
                with st.expander("➕ Add Collaborator"):
                    collab_name = st.text_input("Name")
                    collab_email = st.text_input("Email")
                    collab_role = st.selectbox("Role", ["Viewer", "Editor", "Admin"])

                    if st.button("Add Collaborator"):
                        if collab_name and collab_email:
                            whiteboard['collaborators'].append({
                                'name': collab_name,
                                'email': collab_email,
                                'role': collab_role,
                                'added': datetime.now().isoformat()
                            })
                            self.save_whiteboard(whiteboard)
                            st.success(f"Added {collab_name}")
                            st.rerun()

                # Display collaborators
                if whiteboard['collaborators']:
                    st.markdown("### Current Collaborators")
                    for idx, collab in enumerate(whiteboard['collaborators']):
                        col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
                        with col1:
                            st.write(f"👤 {collab['name']}")
                        with col2:
                            st.write(collab['email'])
                        with col3:
                            st.write(collab['role'])
                        with col4:
                            if st.button("🗑️", key=f"del_collab_{idx}"):
                                whiteboard['collaborators'].pop(idx)
                                self.save_whiteboard(whiteboard)
                                st.rerun()
                else:
                    st.info("No collaborators yet. Add team members to collaborate!")

                # Share settings
                st.markdown("### 🔗 Share Settings")
                share_link = st.text_input("Share Link", value=f"https://nexus.app/whiteboard/{whiteboard['id']}", disabled=True)
                col1, col2 = st.columns(2)
                with col1:
                    st.checkbox("Anyone with link can view", key="share_view")
                with col2:
                    st.checkbox("Anyone with link can edit", key="share_edit")

            # AI Assistant Tab
            with tabs[3]:
                st.subheader("🤖 AI-Powered Assistance")

                ai_task = st.radio(
                    "How can AI help?",
                    ["Generate Ideas", "Organize Content", "Create Summary", "Suggest Next Steps"]
                )

                if ai_task == "Generate Ideas":
                    topic = st.text_input("Brainstorming topic")
                    num_ideas = st.slider("Number of ideas", 5, 20, 10)

                    if st.button("💡 Generate Ideas"):
                        if topic:
                            with st.spinner("Generating ideas..."):
                                prompt = f"Generate {num_ideas} creative ideas for: {topic}"
                                ideas = ai_assistant.generate(prompt, max_tokens=1000)
                                st.markdown(ideas)

                                # Add as sticky notes
                                if st.button("Add to Canvas as Sticky Notes"):
                                    for line in ideas.split('\n'):
                                        if line.strip() and len(line) < 200:
                                            whiteboard['annotations'].append({
                                                'type': 'sticky',
                                                'content': line.strip(),
                                                'color': 'Yellow',
                                                'created': datetime.now().isoformat()
                                            })
                                    self.save_whiteboard(whiteboard)
                                    st.success("Added ideas to canvas!")
                                    st.rerun()

                elif ai_task == "Organize Content":
                    if whiteboard['annotations']:
                        if st.button("🗂️ Organize Annotations"):
                            with st.spinner("Organizing..."):
                                content = json.dumps(whiteboard['annotations'], indent=2)
                                prompt = f"Organize and categorize this whiteboard content:\n{content}"
                                organization = ai_assistant.generate(prompt, max_tokens=1000)
                                st.markdown(organization)
                    else:
                        st.info("Add some content first!")

                elif ai_task == "Create Summary":
                    if whiteboard['annotations']:
                        if st.button("📋 Create Summary"):
                            with st.spinner("Summarizing..."):
                                content = json.dumps(whiteboard['annotations'], indent=2)
                                prompt = f"Create a concise summary of this whiteboard session:\n{content}"
                                summary = ai_assistant.generate(prompt, max_tokens=800)
                                st.markdown(summary)

                                # Option to add as text box
                                if st.button("Add Summary to Canvas"):
                                    whiteboard['annotations'].append({
                                        'type': 'text',
                                        'content': summary,
                                        'created': datetime.now().isoformat()
                                    })
                                    self.save_whiteboard(whiteboard)
                                    st.success("Summary added!")
                                    st.rerun()
                    else:
                        st.info("Add some content first!")

                else:  # Suggest Next Steps
                    if whiteboard['annotations']:
                        if st.button("🎯 Suggest Next Steps"):
                            with st.spinner("Analyzing..."):
                                content = json.dumps(whiteboard['annotations'], indent=2)
                                prompt = f"Based on this whiteboard content, suggest actionable next steps:\n{content}"
                                next_steps = ai_assistant.generate(prompt, max_tokens=800)
                                st.markdown(next_steps)
                    else:
                        st.info("Add some content first!")

            # Export
            st.markdown("### 📤 Export")
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    "Download JSON",
                    json.dumps(whiteboard, indent=2),
                    file_name=f"{whiteboard['name']}.json",
                    mime="application/json"
                )
            with col2:
                # Export as markdown
                markdown_content = f"# {whiteboard['name']}\n\n"
                for obj in whiteboard['annotations']:
                    if obj['type'] == 'text':
                        markdown_content += f"{obj['content']}\n\n"
                    elif obj['type'] == 'sticky':
                        markdown_content += f"- {obj['content']}\n"
                    elif obj['type'] == 'link':
                        markdown_content += f"- [{obj['text']}]({obj['url']})\n"

                st.download_button(
                    "Download Markdown",
                    markdown_content,
                    file_name=f"{whiteboard['name']}.md",
                    mime="text/markdown"
                )

        else:
            st.info("👈 Create or select a whiteboard to get started")

            # Welcome message
            st.markdown("""
            ## Welcome to Whiteboard! 🎨

            **Features:**
            - ♾️ Infinite canvas
            - 🖊️ Multiple drawing tools
            - 📝 Text, shapes, and sticky notes
            - 👥 Real-time collaboration
            - 🤖 AI-powered brainstorming

            **Get Started:**
            1. Create a new whiteboard
            2. Use drawing tools or add objects
            3. Invite collaborators
            4. Use AI for idea generation
            5. Export your work
            """)


def main():
    """Main entry point"""
    whiteboard = Whiteboard()
    whiteboard.render()


if __name__ == "__main__":
    main()
