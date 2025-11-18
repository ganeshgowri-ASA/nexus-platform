"""
Editor Canvas Component

Renders the main rich text editor.
"""

import streamlit as st
from streamlit import components
from typing import Dict, Any, Optional
import json


def render_editor(
    content: Dict[str, Any],
    placeholder: str = "Start writing...",
    height: int = 500,
    readonly: bool = False
) -> Optional[Dict[str, Any]]:
    """
    Render the rich text editor using Quill.

    Args:
        content: Current content in Quill Delta format
        placeholder: Placeholder text
        height: Editor height in pixels
        readonly: Whether editor is read-only

    Returns:
        Updated content from editor or None
    """
    # Try to use streamlit-quill if available
    try:
        from streamlit_quill import st_quill

        # Configure Quill modules
        modules = {
            'toolbar': [
                [{'header': [1, 2, 3, 4, 5, 6, False]}],
                ['bold', 'italic', 'underline', 'strike'],
                [{'color': []}, {'background': []}],
                [{'font': []}],
                [{'align': []}],
                [{'list': 'ordered'}, {'list': 'bullet'}, {'list': 'check'}],
                [{'indent': '-1'}, {'indent': '+1'}],
                ['blockquote', 'code-block'],
                ['link', 'image'],
                [{'script': 'sub'}, {'script': 'super'}],
                ['clean']
            ],
            'clipboard': {
                'matchVisual': False
            }
        }

        # Render Quill editor
        result = st_quill(
            value=content,
            placeholder=placeholder,
            html=False,  # Use Delta format
            readonly=readonly,
            key="quill_editor",
            toolbar=modules['toolbar']
        )

        return result

    except ImportError:
        # Fallback to text area if streamlit-quill is not available
        st.warning("⚠️ streamlit-quill not installed. Using fallback text editor.")
        st.info("To use the rich text editor, install: `pip install streamlit-quill`")

        # Extract plain text from content
        text = ""
        if content and 'ops' in content:
            for op in content['ops']:
                if isinstance(op.get('insert'), str):
                    text += op['insert']

        # Render text area
        new_text = st.text_area(
            "Document Content",
            value=text,
            height=height,
            placeholder=placeholder,
            disabled=readonly,
            key="text_editor"
        )

        # Convert back to Delta format
        if new_text != text:
            return {"ops": [{"insert": new_text}]}

        return None


def render_simple_editor(
    content: str,
    placeholder: str = "Start writing...",
    height: int = 500,
    readonly: bool = False
) -> str:
    """
    Render a simple text editor (fallback).

    Args:
        content: Current content as plain text
        placeholder: Placeholder text
        height: Editor height in pixels
        readonly: Whether editor is read-only

    Returns:
        Updated content
    """
    return st.text_area(
        "Document Content",
        value=content,
        height=height,
        placeholder=placeholder,
        disabled=readonly,
        key="simple_editor",
        label_visibility="collapsed"
    )


def render_html_editor(
    html_content: str,
    height: int = 500
) -> Optional[str]:
    """
    Render an HTML-based editor using custom component.

    Args:
        html_content: Current content as HTML
        height: Editor height in pixels

    Returns:
        Updated HTML content or None
    """
    # Custom HTML editor component
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <link href="https://cdn.quilljs.com/1.3.6/quill.snow.css" rel="stylesheet">
        <script src="https://cdn.quilljs.com/1.3.6/quill.js"></script>
        <style>
            body {{
                margin: 0;
                padding: 10px;
                font-family: Arial, sans-serif;
            }}
            #editor {{
                height: {height - 50}px;
                border: 1px solid #ccc;
                border-radius: 4px;
            }}
            .ql-toolbar {{
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }}
            .ql-container {{
                border-bottom-left-radius: 4px;
                border-bottom-right-radius: 4px;
            }}
        </style>
    </head>
    <body>
        <div id="editor">{html_content}</div>
        <script>
            var quill = new Quill('#editor', {{
                theme: 'snow',
                modules: {{
                    toolbar: [
                        [{{'header': [1, 2, 3, 4, 5, 6, false]}}],
                        ['bold', 'italic', 'underline', 'strike'],
                        [{{'color': []}}, {{'background': []}}],
                        [{{'align': []}}],
                        [{{'list': 'ordered'}}, {{'list': 'bullet'}}],
                        ['blockquote', 'code-block'],
                        ['link', 'image'],
                        ['clean']
                    ]
                }}
            }});

            // Send content updates to Streamlit
            quill.on('text-change', function() {{
                var content = quill.getContents();
                window.parent.postMessage({{
                    type: 'streamlit:setComponentValue',
                    value: content
                }}, '*');
            }});
        </script>
    </body>
    </html>
    """

    # Render custom component
    result = components.html(html, height=height, scrolling=True)

    return result


def render_markdown_editor(
    markdown_content: str,
    height: int = 500
) -> str:
    """
    Render a markdown editor with live preview.

    Args:
        markdown_content: Current content as markdown
        height: Editor height in pixels

    Returns:
        Updated markdown content
    """
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Editor**")
        new_content = st.text_area(
            "Markdown",
            value=markdown_content,
            height=height,
            key="markdown_editor",
            label_visibility="collapsed"
        )

    with col2:
        st.markdown("**Preview**")
        with st.container(height=height):
            st.markdown(new_content)

    return new_content


def render_collaborative_cursors(cursors: Dict[str, Any]) -> None:
    """
    Render collaborative editing cursors.

    Args:
        cursors: Dictionary of user cursors with positions and colors
    """
    if not cursors:
        return

    st.markdown("**Active Users:**")

    for user_id, cursor_info in cursors.items():
        color = cursor_info.get('color', '#000000')
        username = cursor_info.get('username', user_id)

        st.markdown(
            f'<span style="color: {color}; font-weight: bold;">● {username}</span>',
            unsafe_allow_html=True
        )


def render_print_preview(content: Dict[str, Any]) -> None:
    """
    Render print preview of document.

    Args:
        content: Document content in Quill Delta format
    """
    st.markdown("### 📄 Print Preview")

    # Extract text from content
    text = ""
    if content and 'ops' in content:
        for op in content['ops']:
            if isinstance(op.get('insert'), str):
                text += op['insert']

    # Render in a styled container
    st.markdown(
        f"""
        <div style="
            background-color: white;
            color: black;
            padding: 2.54cm;
            margin: 20px auto;
            max-width: 21cm;
            min-height: 29.7cm;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
            font-family: 'Times New Roman', serif;
            font-size: 12pt;
            line-height: 1.5;
        ">
            {text.replace(chr(10), '<br>')}
        </div>
        """,
        unsafe_allow_html=True
    )

    if st.button("🖨️ Print Document"):
        st.info("Print dialog would open here. Use browser's print function (Ctrl+P / Cmd+P)")


def apply_custom_css() -> None:
    """Apply custom CSS for the editor."""
    st.markdown(
        """
        <style>
        /* Editor container styling */
        .editor-container {
            background-color: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        /* Toolbar styling */
        .toolbar {
            background-color: #f8f9fa;
            border-bottom: 1px solid #dee2e6;
            padding: 10px;
            border-radius: 8px 8px 0 0;
        }

        /* Status bar styling */
        .status-bar {
            background-color: #f8f9fa;
            border-top: 1px solid #dee2e6;
            padding: 10px;
            border-radius: 0 0 8px 8px;
            font-size: 14px;
        }

        /* Button styling */
        .stButton button {
            border-radius: 4px;
            transition: all 0.3s ease;
        }

        .stButton button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }

        /* Metric styling */
        [data-testid="stMetric"] {
            background-color: transparent;
        }

        /* Expander styling */
        .streamlit-expanderHeader {
            background-color: #f8f9fa;
            border-radius: 4px;
        }

        /* Text area styling */
        .stTextArea textarea {
            font-family: 'Georgia', serif;
            font-size: 14px;
            line-height: 1.6;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
