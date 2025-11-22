"""
Session 37: Mind Map Editor
Features: Nodes, branches, export, AI-powered generation
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


class MindMapEditor:
    """Mind Map Editor with nodes, branches, and AI assistance"""

    def __init__(self):
        """Initialize mind map editor"""
        if 'mindmaps' not in st.session_state:
            st.session_state.mindmaps = self.load_mindmaps()
        if 'current_mindmap' not in st.session_state:
            st.session_state.current_mindmap = None

    def load_mindmaps(self) -> List[Dict]:
        """Load saved mind maps"""
        mindmaps = []
        files = storage.list_files('mindmaps', '.json')
        for file in files:
            data = storage.load_json(file, 'mindmaps')
            if data:
                mindmaps.append(data)
        return mindmaps

    def save_mindmap(self, mindmap: Dict) -> bool:
        """Save mind map"""
        filename = f"mindmap_{mindmap['id']}.json"
        return storage.save_json(filename, mindmap, 'mindmaps')

    def create_mindmap(self, name: str, central_topic: str) -> Dict:
        """Create new mind map"""
        mindmap = {
            'id': datetime.now().strftime('%Y%m%d_%H%M%S'),
            'name': name,
            'central_topic': central_topic,
            'created': datetime.now().isoformat(),
            'modified': datetime.now().isoformat(),
            'nodes': {
                'root': {
                    'id': 'root',
                    'text': central_topic,
                    'level': 0,
                    'children': []
                }
            }
        }
        return mindmap

    def add_node(self, mindmap: Dict, parent_id: str, text: str) -> str:
        """Add node to mind map"""
        node_id = f"node_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        parent_level = mindmap['nodes'][parent_id]['level']

        mindmap['nodes'][node_id] = {
            'id': node_id,
            'text': text,
            'level': parent_level + 1,
            'parent': parent_id,
            'children': []
        }

        mindmap['nodes'][parent_id]['children'].append(node_id)
        mindmap['modified'] = datetime.now().isoformat()
        return node_id

    def delete_node(self, mindmap: Dict, node_id: str):
        """Delete node and its children"""
        if node_id == 'root':
            return  # Cannot delete root

        node = mindmap['nodes'][node_id]

        # Delete all children recursively
        for child_id in node.get('children', []):
            self.delete_node(mindmap, child_id)

        # Remove from parent's children list
        parent_id = node.get('parent')
        if parent_id and parent_id in mindmap['nodes']:
            mindmap['nodes'][parent_id]['children'].remove(node_id)

        # Delete the node
        del mindmap['nodes'][node_id]
        mindmap['modified'] = datetime.now().isoformat()

    def generate_mermaid(self, mindmap: Dict) -> str:
        """Generate Mermaid mindmap diagram"""
        lines = ["mindmap"]
        lines.append(f"  root(({mindmap['central_topic']}))")

        def add_children(parent_id: str, indent: int):
            node = mindmap['nodes'][parent_id]
            for child_id in node.get('children', []):
                child = mindmap['nodes'][child_id]
                lines.append("  " * indent + f"{child_id}[{child['text']}]")
                add_children(child_id, indent + 1)

        add_children('root', 2)
        return "\n".join(lines)

    def export_to_markdown(self, mindmap: Dict) -> str:
        """Export mind map to markdown"""
        lines = [f"# {mindmap['name']}", "", f"**Central Topic:** {mindmap['central_topic']}", ""]

        def add_children(parent_id: str, level: int):
            node = mindmap['nodes'][parent_id]
            for child_id in node.get('children', []):
                child = mindmap['nodes'][child_id]
                lines.append("  " * level + f"- {child['text']}")
                add_children(child_id, level + 1)

        add_children('root', 0)
        return "\n".join(lines)

    def render(self):
        """Render mind map editor"""
        st.title("🧠 Mind Map Editor")
        st.markdown("*Create and organize ideas with interactive mind maps*")

        # Sidebar
        with st.sidebar:
            st.header("Mind Map Manager")

            # New mind map
            with st.expander("➕ New Mind Map", expanded=False):
                new_name = st.text_input("Mind Map Name", key="new_mindmap_name")
                central_topic = st.text_input("Central Topic", key="central_topic")
                if st.button("Create Mind Map", type="primary"):
                    if new_name and central_topic:
                        mindmap = self.create_mindmap(new_name, central_topic)
                        st.session_state.mindmaps.append(mindmap)
                        st.session_state.current_mindmap = mindmap
                        self.save_mindmap(mindmap)
                        st.success(f"Created '{new_name}'")
                        st.rerun()

            # Existing mind maps
            if st.session_state.mindmaps:
                st.subheader("Saved Mind Maps")
                for mindmap in st.session_state.mindmaps:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        if st.button(mindmap['name'], key=f"load_{mindmap['id']}"):
                            st.session_state.current_mindmap = mindmap
                            st.rerun()
                    with col2:
                        if st.button("🗑️", key=f"del_{mindmap['id']}"):
                            storage.delete_file(f"mindmap_{mindmap['id']}.json", 'mindmaps')
                            st.session_state.mindmaps.remove(mindmap)
                            st.rerun()

        # Main editor
        if st.session_state.current_mindmap:
            mindmap = st.session_state.current_mindmap

            tabs = st.tabs(["🌳 Mind Map", "🤖 AI Assistant", "📤 Export"])

            # Mind Map Tab
            with tabs[0]:
                st.subheader(f"Mind Map: {mindmap['name']}")
                st.caption(f"Central Topic: {mindmap['central_topic']}")

                col1, col2 = st.columns([2, 1])

                with col1:
                    st.markdown("### Mind Map Structure")

                    # Display mind map as tree
                    def display_node(node_id: str, level: int = 0):
                        node = mindmap['nodes'][node_id]
                        indent = "  " * level

                        # Node display
                        col_a, col_b, col_c = st.columns([level + 1, 4, 1])

                        with col_b:
                            if level == 0:
                                st.markdown(f"### 🎯 {node['text']}")
                            else:
                                st.markdown(f"{indent}{'📌' if level == 1 else '•'} **{node['text']}**")

                        with col_c:
                            if node_id != 'root':
                                if st.button("❌", key=f"del_node_{node_id}"):
                                    self.delete_node(mindmap, node_id)
                                    self.save_mindmap(mindmap)
                                    st.rerun()

                        # Display children
                        for child_id in node.get('children', []):
                            display_node(child_id, level + 1)

                    display_node('root')

                    # Visualize as Mermaid
                    st.markdown("### Visual Representation")
                    mermaid_code = self.generate_mermaid(mindmap)
                    st.code(mermaid_code, language='mermaid')

                    # Try to render
                    try:
                        import streamlit.components.v1 as components
                        mermaid_html = f"""
                        <html>
                        <head>
                            <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
                            <script>mermaid.initialize({{startOnLoad:true}});</script>
                        </head>
                        <body>
                            <div class="mermaid">
                                {mermaid_code}
                            </div>
                        </body>
                        </html>
                        """
                        components.html(mermaid_html, height=400)
                    except:
                        st.info("Visual rendering requires mermaid support")

                with col2:
                    st.markdown("### Add Node")

                    # Select parent
                    node_options = {node_id: node['text'] for node_id, node in mindmap['nodes'].items()}
                    parent_id = st.selectbox(
                        "Parent Node",
                        options=list(node_options.keys()),
                        format_func=lambda x: node_options[x],
                        key="parent_select"
                    )

                    new_node_text = st.text_input("Node Text", key="new_node_text")

                    if st.button("➕ Add Node", type="primary"):
                        if new_node_text:
                            self.add_node(mindmap, parent_id, new_node_text)
                            self.save_mindmap(mindmap)
                            st.success("Node added!")
                            st.rerun()

                    # Statistics
                    st.markdown("### 📊 Statistics")
                    total_nodes = len(mindmap['nodes'])
                    max_level = max(node['level'] for node in mindmap['nodes'].values())
                    st.metric("Total Nodes", total_nodes)
                    st.metric("Max Depth", max_level)

            # AI Assistant Tab
            with tabs[1]:
                st.subheader("🤖 AI-Powered Mind Map Generation")

                ai_mode = st.radio(
                    "AI Mode",
                    ["Generate from Topic", "Expand Existing Node", "Suggest Ideas"]
                )

                if ai_mode == "Generate from Topic":
                    topic = st.text_input("Topic", value=mindmap['central_topic'])
                    num_branches = st.slider("Number of main branches", 3, 10, 5)

                    if st.button("✨ Generate Mind Map", type="primary"):
                        with st.spinner("Generating mind map..."):
                            result = ai_assistant.generate_mindmap(topic)

                            if result and 'branches' in result:
                                # Clear existing nodes except root
                                mindmap['nodes'] = {
                                    'root': {
                                        'id': 'root',
                                        'text': topic,
                                        'level': 0,
                                        'children': []
                                    }
                                }
                                mindmap['central_topic'] = topic

                                # Add branches
                                for branch in result['branches'][:num_branches]:
                                    branch_id = self.add_node(mindmap, 'root', branch.get('name', 'Branch'))

                                    # Add children
                                    for child in branch.get('children', [])[:3]:
                                        self.add_node(mindmap, branch_id, child)

                                self.save_mindmap(mindmap)
                                st.success("Mind map generated!")
                                st.rerun()

                elif ai_mode == "Expand Existing Node":
                    node_options = {node_id: node['text'] for node_id, node in mindmap['nodes'].items()}
                    expand_node_id = st.selectbox(
                        "Select Node to Expand",
                        options=list(node_options.keys()),
                        format_func=lambda x: node_options[x]
                    )
                    num_ideas = st.slider("Number of ideas", 2, 8, 3)

                    if st.button("💡 Generate Ideas"):
                        node_text = mindmap['nodes'][expand_node_id]['text']
                        with st.spinner(f"Generating ideas for '{node_text}'..."):
                            prompt = f"Generate {num_ideas} related sub-topics or ideas for: {node_text}"
                            response = ai_assistant.generate(prompt, max_tokens=500)

                            # Parse response (simple line-based parsing)
                            lines = [line.strip('- ').strip() for line in response.split('\n') if line.strip()]
                            for line in lines[:num_ideas]:
                                if line and len(line) < 100:
                                    self.add_node(mindmap, expand_node_id, line)

                            self.save_mindmap(mindmap)
                            st.success(f"Added {min(len(lines), num_ideas)} ideas!")
                            st.rerun()

                else:  # Suggest Ideas
                    context = st.text_area("What are you trying to brainstorm?")
                    if st.button("Get Suggestions"):
                        if context:
                            with st.spinner("Generating suggestions..."):
                                suggestions = ai_assistant.generate(
                                    f"Provide creative suggestions and ideas for: {context}",
                                    max_tokens=1000
                                )
                                st.markdown(suggestions)

            # Export Tab
            with tabs[2]:
                st.subheader("📤 Export Mind Map")

                export_format = st.selectbox(
                    "Export Format",
                    ["Markdown", "JSON", "Mermaid", "Plain Text"]
                )

                if export_format == "Markdown":
                    content = self.export_to_markdown(mindmap)
                    st.code(content, language='markdown')
                    st.download_button(
                        "Download Markdown",
                        content,
                        file_name=f"{mindmap['name']}.md",
                        mime="text/markdown"
                    )

                elif export_format == "JSON":
                    content = json.dumps(mindmap, indent=2)
                    st.code(content, language='json')
                    st.download_button(
                        "Download JSON",
                        content,
                        file_name=f"{mindmap['name']}.json",
                        mime="application/json"
                    )

                elif export_format == "Mermaid":
                    content = self.generate_mermaid(mindmap)
                    st.code(content, language='mermaid')
                    st.download_button(
                        "Download Mermaid",
                        content,
                        file_name=f"{mindmap['name']}.mmd",
                        mime="text/plain"
                    )

                else:  # Plain Text
                    content = self.export_to_markdown(mindmap).replace('#', '').replace('*', '')
                    st.text_area("Plain Text", content, height=300)
                    st.download_button(
                        "Download Text",
                        content,
                        file_name=f"{mindmap['name']}.txt",
                        mime="text/plain"
                    )

        else:
            st.info("👈 Create or select a mind map to get started")

            # Welcome message
            st.markdown("""
            ## Welcome to Mind Map Editor! 🧠

            **Features:**
            - 🌳 Hierarchical node structure
            - 📌 Unlimited branches and depth
            - 🤖 AI-powered idea generation
            - 📤 Multiple export formats
            - 💡 Smart suggestions

            **Get Started:**
            1. Create a new mind map with a central topic
            2. Add branches and sub-branches
            3. Use AI to expand ideas automatically
            4. Export in your preferred format
            """)


def main():
    """Main entry point"""
    editor = MindMapEditor()
    editor.render()


if __name__ == "__main__":
    main()
