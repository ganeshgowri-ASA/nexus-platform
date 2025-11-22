"""
Session 36: Flowchart Editor
Features: Drag-drop shapes, Mermaid support, AI-powered generation
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


class FlowchartEditor:
    """Flowchart Editor with drag-drop and Mermaid support"""

    def __init__(self):
        """Initialize flowchart editor"""
        if 'flowcharts' not in st.session_state:
            st.session_state.flowcharts = self.load_flowcharts()
        if 'current_flowchart' not in st.session_state:
            st.session_state.current_flowchart = None
        if 'flowchart_elements' not in st.session_state:
            st.session_state.flowchart_elements = []

    def load_flowcharts(self) -> List[Dict]:
        """Load saved flowcharts"""
        flowcharts = []
        files = storage.list_files('flowcharts', '.json')
        for file in files:
            data = storage.load_json(file, 'flowcharts')
            if data:
                flowcharts.append(data)
        return flowcharts

    def save_flowchart(self, flowchart: Dict) -> bool:
        """Save flowchart"""
        filename = f"flowchart_{flowchart['id']}.json"
        return storage.save_json(filename, flowchart, 'flowcharts')

    def create_flowchart(self, name: str, description: str = "") -> Dict:
        """Create new flowchart"""
        flowchart = {
            'id': datetime.now().strftime('%Y%m%d_%H%M%S'),
            'name': name,
            'description': description,
            'created': datetime.now().isoformat(),
            'modified': datetime.now().isoformat(),
            'mermaid_code': 'graph TD\n    Start[Start] --> End[End]',
            'elements': [],
            'connections': []
        }
        return flowchart

    def mermaid_shapes(self) -> Dict[str, str]:
        """Available Mermaid shapes"""
        return {
            'Rectangle': 'A[Text]',
            'Rounded': 'A(Text)',
            'Stadium': 'A([Text])',
            'Subroutine': 'A[[Text]]',
            'Cylindrical': 'A[(Text)]',
            'Circle': 'A((Text))',
            'Asymmetric': 'A>Text]',
            'Rhombus': 'A{Text}',
            'Hexagon': 'A{{Text}}',
            'Parallelogram': 'A[/Text/]',
            'Trapezoid': 'A[\\Text\\]'
        }

    def render(self):
        """Render flowchart editor"""
        st.title("🔄 Flowchart Editor")
        st.markdown("*Create flowcharts with drag-drop shapes and Mermaid support*")

        # Sidebar
        with st.sidebar:
            st.header("Flowchart Manager")

            # New flowchart
            with st.expander("➕ New Flowchart", expanded=False):
                new_name = st.text_input("Flowchart Name", key="new_flowchart_name")
                new_desc = st.text_area("Description", key="new_flowchart_desc")
                if st.button("Create Flowchart", type="primary"):
                    if new_name:
                        flowchart = self.create_flowchart(new_name, new_desc)
                        st.session_state.flowcharts.append(flowchart)
                        st.session_state.current_flowchart = flowchart
                        self.save_flowchart(flowchart)
                        st.success(f"Created '{new_name}'")
                        st.rerun()

            # Existing flowcharts
            if st.session_state.flowcharts:
                st.subheader("Saved Flowcharts")
                for flowchart in st.session_state.flowcharts:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        if st.button(flowchart['name'], key=f"load_{flowchart['id']}"):
                            st.session_state.current_flowchart = flowchart
                            st.rerun()
                    with col2:
                        if st.button("🗑️", key=f"del_{flowchart['id']}"):
                            storage.delete_file(f"flowchart_{flowchart['id']}.json", 'flowcharts')
                            st.session_state.flowcharts.remove(flowchart)
                            st.rerun()

        # Main editor
        if st.session_state.current_flowchart:
            flowchart = st.session_state.current_flowchart

            tabs = st.tabs(["📝 Visual Editor", "💻 Mermaid Code", "🤖 AI Assistant", "🎨 Shapes"])

            # Visual Editor Tab
            with tabs[0]:
                st.subheader(f"Editing: {flowchart['name']}")
                st.caption(flowchart['description'])

                col1, col2 = st.columns([2, 1])

                with col1:
                    st.markdown("### Flowchart Preview")
                    # Render Mermaid diagram
                    st.code(flowchart['mermaid_code'], language='mermaid')

                    # Try to render with mermaid
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
                                {flowchart['mermaid_code']}
                            </div>
                        </body>
                        </html>
                        """
                        components.html(mermaid_html, height=400)
                    except:
                        st.info("Install mermaid renderer for live preview")

                with col2:
                    st.markdown("### Quick Actions")

                    # Add element
                    shape_type = st.selectbox("Shape", list(self.mermaid_shapes().keys()))
                    element_id = st.text_input("ID", value=f"node{len(flowchart['elements'])+1}")
                    element_text = st.text_input("Text", value="New Node")

                    if st.button("Add Element", type="primary"):
                        flowchart['elements'].append({
                            'id': element_id,
                            'text': element_text,
                            'shape': shape_type
                        })
                        flowchart['modified'] = datetime.now().isoformat()
                        self.save_flowchart(flowchart)
                        st.success("Element added")
                        st.rerun()

                    # Add connection
                    if flowchart['elements']:
                        st.markdown("#### Add Connection")
                        element_ids = [e['id'] for e in flowchart['elements']]
                        from_node = st.selectbox("From", element_ids, key="from_node")
                        to_node = st.selectbox("To", element_ids, key="to_node")
                        connection_label = st.text_input("Label (optional)", key="conn_label")
                        arrow_type = st.selectbox("Arrow", ["-->", "-.->", "==>"])

                        if st.button("Add Connection"):
                            flowchart['connections'].append({
                                'from': from_node,
                                'to': to_node,
                                'label': connection_label,
                                'arrow': arrow_type
                            })
                            flowchart['modified'] = datetime.now().isoformat()
                            self.save_flowchart(flowchart)
                            st.success("Connection added")
                            st.rerun()

                # Elements list
                if flowchart['elements']:
                    st.markdown("### Elements")
                    for idx, elem in enumerate(flowchart['elements']):
                        col1, col2, col3, col4 = st.columns([1, 2, 2, 1])
                        with col1:
                            st.write(f"**{elem['id']}**")
                        with col2:
                            st.write(elem['text'])
                        with col3:
                            st.write(elem['shape'])
                        with col4:
                            if st.button("❌", key=f"del_elem_{idx}"):
                                flowchart['elements'].pop(idx)
                                flowchart['modified'] = datetime.now().isoformat()
                                self.save_flowchart(flowchart)
                                st.rerun()

            # Mermaid Code Tab
            with tabs[1]:
                st.subheader("Mermaid Code Editor")
                st.markdown("Edit the Mermaid code directly for full control")

                mermaid_code = st.text_area(
                    "Mermaid Code",
                    value=flowchart['mermaid_code'],
                    height=400,
                    key="mermaid_editor"
                )

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("💾 Save Code", type="primary"):
                        flowchart['mermaid_code'] = mermaid_code
                        flowchart['modified'] = datetime.now().isoformat()
                        self.save_flowchart(flowchart)
                        st.success("Code saved!")

                with col2:
                    if st.button("🔄 Reset to Default"):
                        flowchart['mermaid_code'] = 'graph TD\n    Start[Start] --> End[End]'
                        self.save_flowchart(flowchart)
                        st.rerun()

                # Documentation
                with st.expander("📚 Mermaid Syntax Help"):
                    st.markdown("""
                    **Basic Syntax:**
                    ```
                    graph TD
                        A[Rectangle] --> B{Decision}
                        B -->|Yes| C[Result 1]
                        B -->|No| D[Result 2]
                    ```

                    **Graph Directions:**
                    - `TD` or `TB`: Top to bottom
                    - `BT`: Bottom to top
                    - `LR`: Left to right
                    - `RL`: Right to left

                    **Node Shapes:**
                    - `[Rectangle]`
                    - `(Rounded)`
                    - `{Diamond}`
                    - `((Circle))`
                    - `[[Subroutine]]`

                    **Connection Types:**
                    - `-->` Solid arrow
                    - `-.->` Dotted arrow
                    - `==>` Thick arrow
                    - `--text-->` Labeled arrow
                    """)

            # AI Assistant Tab
            with tabs[2]:
                st.subheader("🤖 AI-Powered Flowchart Generation")

                ai_description = st.text_area(
                    "Describe your flowchart",
                    placeholder="E.g., Create a flowchart for a user login process with validation and error handling",
                    height=100
                )

                col1, col2 = st.columns([1, 3])
                with col1:
                    if st.button("✨ Generate Flowchart", type="primary"):
                        if ai_description:
                            with st.spinner("Generating flowchart..."):
                                mermaid_code = ai_assistant.generate_flowchart(ai_description)
                                flowchart['mermaid_code'] = mermaid_code
                                flowchart['description'] = ai_description
                                flowchart['modified'] = datetime.now().isoformat()
                                self.save_flowchart(flowchart)
                                st.success("Flowchart generated!")
                                st.rerun()
                        else:
                            st.warning("Please provide a description")

                # Show AI suggestions
                if ai_description:
                    with st.expander("💡 AI Suggestions"):
                        suggestions = ai_assistant.generate(
                            f"Provide 3 specific suggestions to improve this flowchart: {ai_description}",
                            max_tokens=500
                        )
                        st.markdown(suggestions)

            # Shapes Reference Tab
            with tabs[3]:
                st.subheader("🎨 Available Shapes")

                shapes = self.mermaid_shapes()
                cols = st.columns(2)

                for idx, (name, syntax) in enumerate(shapes.items()):
                    with cols[idx % 2]:
                        st.markdown(f"**{name}**")
                        st.code(syntax, language='mermaid')
                        st.markdown("---")

            # Export options
            st.markdown("### 📤 Export")
            col1, col2, col3 = st.columns(3)

            with col1:
                st.download_button(
                    "Download Mermaid",
                    flowchart['mermaid_code'],
                    file_name=f"{flowchart['name']}.mmd",
                    mime="text/plain"
                )

            with col2:
                st.download_button(
                    "Download JSON",
                    json.dumps(flowchart, indent=2),
                    file_name=f"{flowchart['name']}.json",
                    mime="application/json"
                )

            with col3:
                st.download_button(
                    "Download Markdown",
                    f"# {flowchart['name']}\n\n{flowchart['description']}\n\n```mermaid\n{flowchart['mermaid_code']}\n```",
                    file_name=f"{flowchart['name']}.md",
                    mime="text/markdown"
                )

        else:
            st.info("👈 Create or select a flowchart to get started")

            # Welcome message
            st.markdown("""
            ## Welcome to Flowchart Editor! 🔄

            **Features:**
            - 📐 Visual drag-drop interface
            - 💻 Mermaid syntax support
            - 🤖 AI-powered flowchart generation
            - 📤 Multiple export formats
            - 🎨 Rich shape library

            **Get Started:**
            1. Create a new flowchart using the sidebar
            2. Add shapes and connections visually
            3. Or use AI to generate flowcharts from descriptions
            4. Export in Mermaid, JSON, or Markdown formats
            """)


def main():
    """Main entry point"""
    editor = FlowchartEditor()
    editor.render()


if __name__ == "__main__":
    main()
