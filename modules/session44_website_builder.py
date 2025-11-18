"""
Session 44: Website Builder
Features: Drag-drop, responsive design, SEO optimization, AI content generation
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


class WebsiteBuilder:
    """Drag-drop website builder with SEO and AI"""

    def __init__(self):
        """Initialize website builder"""
        if 'websites' not in st.session_state:
            st.session_state.websites = self.load_websites()
        if 'current_website' not in st.session_state:
            st.session_state.current_website = None

    def load_websites(self) -> List[Dict]:
        """Load saved websites"""
        websites = []
        files = storage.list_files('websites', '.json')
        for file in files:
            data = storage.load_json(file, 'websites')
            if data:
                websites.append(data)
        return websites

    def save_website(self, website: Dict) -> bool:
        """Save website"""
        filename = f"website_{website['id']}.json"
        return storage.save_json(filename, website, 'websites')

    def create_website(self, name: str, template: str) -> Dict:
        """Create new website"""
        return {
            'id': datetime.now().strftime('%Y%m%d_%H%M%S'),
            'name': name,
            'template': template,
            'created': datetime.now().isoformat(),
            'modified': datetime.now().isoformat(),
            'pages': [],
            'components': [],
            'seo': {
                'title': name,
                'description': '',
                'keywords': []
            },
            'style': {
                'theme': 'light',
                'primaryColor': '#007bff',
                'font': 'Arial'
            }
        }

    def templates(self) -> Dict[str, str]:
        """Available templates"""
        return {
            'Business': 'Professional business website',
            'Portfolio': 'Creative portfolio showcase',
            'Blog': 'Personal or professional blog',
            'E-commerce': 'Online store',
            'Landing Page': 'Single page marketing site',
            'Documentation': 'Technical documentation'
        }

    def components(self) -> List[str]:
        """Available components"""
        return [
            'Header/Navigation',
            'Hero Section',
            'Features Grid',
            'Testimonials',
            'Pricing Table',
            'Contact Form',
            'Footer',
            'Image Gallery',
            'Video Section',
            'FAQ Accordion',
            'Call to Action',
            'Team Section'
        ]

    def render(self):
        """Render website builder"""
        st.title("🌐 Website Builder")
        st.markdown("*Build responsive websites with drag-drop, SEO, and AI assistance*")

        # Sidebar
        with st.sidebar:
            st.header("Websites")

            with st.expander("➕ New Website", expanded=False):
                new_name = st.text_input("Website Name", key="new_website_name")
                template = st.selectbox("Template", list(self.templates().keys()), format_func=lambda x: f"{x} - {self.templates()[x]}")
                if st.button("Create Website", type="primary"):
                    if new_name:
                        website = self.create_website(new_name, template)
                        st.session_state.websites.append(website)
                        st.session_state.current_website = website
                        self.save_website(website)
                        st.success(f"Created '{new_name}'")
                        st.rerun()

            if st.session_state.websites:
                for website in st.session_state.websites:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        if st.button(website['name'], key=f"load_{website['id']}"):
                            st.session_state.current_website = website
                            st.rerun()
                    with col2:
                        if st.button("🗑️", key=f"del_{website['id']}"):
                            storage.delete_file(f"website_{website['id']}.json", 'websites')
                            st.session_state.websites.remove(website)
                            st.rerun()

        if st.session_state.current_website:
            website = st.session_state.current_website

            tabs = st.tabs(["📄 Pages", "🧩 Components", "🎨 Design", "🔍 SEO", "🤖 AI Content", "👁️ Preview", "📤 Export"])

            with tabs[0]:
                st.subheader(f"Website: {website['name']}")

                with st.expander("➕ Add Page", expanded=True):
                    page_name = st.text_input("Page Name")
                    page_url = st.text_input("URL Path", placeholder="/about")

                    if st.button("Create Page"):
                        if page_name:
                            website['pages'].append({
                                'name': page_name,
                                'url': page_url,
                                'sections': [],
                                'created': datetime.now().isoformat()
                            })
                            self.save_website(website)
                            st.success(f"Page '{page_name}' created!")
                            st.rerun()

                # Display pages
                if website['pages']:
                    st.markdown("### Pages")
                    for idx, page in enumerate(website['pages']):
                        with st.expander(f"📄 {page['name']} ({page['url']})"):
                            # Edit page content
                            page_title = st.text_input("Page Title", value=page.get('title', ''), key=f"page_title_{idx}")
                            page_content = st.text_area("Content", value=page.get('content', ''), height=200, key=f"page_content_{idx}")

                            website['pages'][idx]['title'] = page_title
                            website['pages'][idx]['content'] = page_content

                            col1, col2 = st.columns([1, 4])
                            with col1:
                                if st.button("🗑️ Delete", key=f"del_page_{idx}"):
                                    website['pages'].pop(idx)
                                    self.save_website(website)
                                    st.rerun()

                    if st.button("💾 Save All Pages"):
                        website['modified'] = datetime.now().isoformat()
                        self.save_website(website)
                        st.success("Pages saved!")

            with tabs[1]:
                st.subheader("🧩 Add Components")

                st.markdown("Drag and drop components to build your pages")

                selected_component = st.selectbox("Select Component", self.components())

                # Component configuration based on type
                if selected_component == 'Header/Navigation':
                    logo_text = st.text_input("Logo Text")
                    nav_items = st.text_area("Navigation Items (one per line)")

                elif selected_component == 'Hero Section':
                    hero_title = st.text_input("Hero Title")
                    hero_subtitle = st.text_input("Hero Subtitle")
                    cta_text = st.text_input("Call-to-Action Button Text")

                elif selected_component == 'Features Grid':
                    num_features = st.number_input("Number of Features", 1, 12, 3)

                elif selected_component == 'Contact Form':
                    form_fields = st.multiselect("Form Fields", ["Name", "Email", "Phone", "Message", "Company"])

                if st.button("Add Component to Website"):
                    component_data = {
                        'type': selected_component,
                        'created': datetime.now().isoformat(),
                        'data': {}
                    }
                    website['components'].append(component_data)
                    self.save_website(website)
                    st.success(f"Added {selected_component}!")
                    st.rerun()

                # Display components
                if website['components']:
                    st.markdown("### Current Components")
                    for idx, comp in enumerate(website['components']):
                        col1, col2 = st.columns([4, 1])
                        with col1:
                            st.write(f"🧩 {comp['type']}")
                        with col2:
                            if st.button("🗑️", key=f"del_comp_{idx}"):
                                website['components'].pop(idx)
                                self.save_website(website)
                                st.rerun()

            with tabs[2]:
                st.subheader("🎨 Design & Styling")

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("### Theme")
                    theme = st.radio("Theme", ["Light", "Dark", "Custom"], index=0 if website['style']['theme'] == 'light' else 1)
                    website['style']['theme'] = theme.lower()

                    primary_color = st.color_picker("Primary Color", website['style']['primaryColor'])
                    website['style']['primaryColor'] = primary_color

                with col2:
                    st.markdown("### Typography")
                    font = st.selectbox("Font Family", ["Arial", "Helvetica", "Georgia", "Roboto", "Open Sans", "Lato"])
                    website['style']['font'] = font

                    font_size = st.slider("Base Font Size", 12, 24, 16)
                    website['style']['fontSize'] = font_size

                # Responsive design
                st.markdown("### 📱 Responsive Design")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.checkbox("Mobile Optimized", value=True)
                with col2:
                    st.checkbox("Tablet Optimized", value=True)
                with col3:
                    st.checkbox("Desktop Optimized", value=True)

                if st.button("💾 Save Design"):
                    website['modified'] = datetime.now().isoformat()
                    self.save_website(website)
                    st.success("Design saved!")

            with tabs[3]:
                st.subheader("🔍 SEO Optimization")

                seo_title = st.text_input("SEO Title", value=website['seo']['title'])
                seo_desc = st.text_area("Meta Description", value=website['seo']['description'], max_chars=160)
                seo_keywords = st.text_input("Keywords (comma-separated)", value=", ".join(website['seo'].get('keywords', [])))

                website['seo']['title'] = seo_title
                website['seo']['description'] = seo_desc
                website['seo']['keywords'] = [k.strip() for k in seo_keywords.split(',') if k.strip()]

                # SEO analysis
                st.markdown("### 📊 SEO Score")

                score = 0
                if seo_title and len(seo_title) > 10:
                    score += 20
                if seo_desc and len(seo_desc) > 50:
                    score += 20
                if website['seo']['keywords']:
                    score += 20
                if website['pages']:
                    score += 20
                if website['components']:
                    score += 20

                st.progress(score / 100)
                st.metric("SEO Score", f"{score}/100")

                # Recommendations
                st.markdown("### 💡 SEO Recommendations")
                recommendations = []
                if not seo_title or len(seo_title) < 10:
                    recommendations.append("❌ Add a descriptive SEO title (50-60 characters)")
                else:
                    recommendations.append("✅ SEO title looks good")

                if not seo_desc or len(seo_desc) < 50:
                    recommendations.append("❌ Write a compelling meta description (150-160 characters)")
                else:
                    recommendations.append("✅ Meta description is well-formed")

                if not website['seo']['keywords']:
                    recommendations.append("❌ Add relevant keywords")
                else:
                    recommendations.append("✅ Keywords are defined")

                for rec in recommendations:
                    st.markdown(rec)

                if st.button("💾 Save SEO Settings"):
                    self.save_website(website)
                    st.success("SEO settings saved!")

            with tabs[4]:
                st.subheader("🤖 AI Content Generator")

                content_type = st.selectbox(
                    "Content Type",
                    ["Page Content", "Product Description", "Hero Section", "About Us", "Blog Post"]
                )

                purpose = st.text_input("Website Purpose/Industry")
                style = st.selectbox("Writing Style", ["Professional", "Casual", "Technical", "Creative"])

                if st.button("✨ Generate Content"):
                    if purpose:
                        with st.spinner("Generating content..."):
                            result = ai_assistant.generate_website_content(purpose, style)

                            if isinstance(result, dict):
                                st.json(result)
                            else:
                                st.markdown(result)

                            if st.button("💾 Add to Website"):
                                # Add generated content to a new page
                                website['pages'].append({
                                    'name': 'AI Generated Content',
                                    'url': '/ai-content',
                                    'content': json.dumps(result) if isinstance(result, dict) else result,
                                    'created': datetime.now().isoformat()
                                })
                                self.save_website(website)
                                st.success("Content added!")
                                st.rerun()

                # Generate specific elements
                st.markdown("### Generate Specific Elements")
                element = st.selectbox("Element", ["Headline", "Tagline", "Call-to-Action", "Feature List"])

                if st.button(f"Generate {element}"):
                    with st.spinner(f"Generating {element}..."):
                        prompt = f"Generate a compelling {element} for a {purpose} website with a {style} tone"
                        content = ai_assistant.generate(prompt, max_tokens=200)
                        st.markdown(content)

            with tabs[5]:
                st.subheader("👁️ Preview")

                # Generate HTML preview
                html_preview = f"""
                <html>
                <head>
                    <title>{website['seo']['title']}</title>
                    <meta name="description" content="{website['seo']['description']}">
                    <style>
                        body {{
                            font-family: {website['style']['font']}, sans-serif;
                            margin: 0;
                            padding: 20px;
                            background-color: {'#f5f5f5' if website['style']['theme'] == 'light' else '#1a1a1a'};
                            color: {'#333' if website['style']['theme'] == 'light' else '#fff'};
                        }}
                        .page {{
                            max-width: 1200px;
                            margin: 0 auto;
                            background: {'white' if website['style']['theme'] == 'light' else '#2a2a2a'};
                            padding: 30px;
                            border-radius: 8px;
                            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                        }}
                        h1 {{
                            color: {website['style']['primaryColor']};
                        }}
                        .component {{
                            margin: 20px 0;
                            padding: 15px;
                            border-left: 3px solid {website['style']['primaryColor']};
                        }}
                    </style>
                </head>
                <body>
                    <div class="page">
                        <h1>{website['name']}</h1>
                """

                for page in website['pages']:
                    html_preview += f"""
                        <div class="page-section">
                            <h2>{page['name']}</h2>
                            <p>{page.get('content', '')}</p>
                        </div>
                    """

                for comp in website['components']:
                    html_preview += f"""
                        <div class="component">
                            <strong>{comp['type']}</strong>
                        </div>
                    """

                html_preview += """
                    </div>
                </body>
                </html>
                """

                st.components.v1.html(html_preview, height=600, scrolling=True)

            with tabs[6]:
                st.subheader("📤 Export Website")

                export_format = st.selectbox("Export Format", ["HTML", "JSON", "Markdown"])

                if export_format == "HTML":
                    # Generate complete HTML
                    html_content = html_preview  # Use the preview HTML
                    st.code(html_content, language='html')
                    st.download_button(
                        "Download HTML",
                        html_content,
                        file_name=f"{website['name']}.html",
                        mime="text/html"
                    )

                elif export_format == "JSON":
                    json_content = json.dumps(website, indent=2)
                    st.code(json_content, language='json')
                    st.download_button(
                        "Download JSON",
                        json_content,
                        file_name=f"{website['name']}.json",
                        mime="application/json"
                    )

                else:  # Markdown
                    md_content = f"# {website['name']}\n\n"
                    for page in website['pages']:
                        md_content += f"## {page['name']}\n\n{page.get('content', '')}\n\n"

                    st.code(md_content, language='markdown')
                    st.download_button(
                        "Download Markdown",
                        md_content,
                        file_name=f"{website['name']}.md",
                        mime="text/markdown"
                    )

        else:
            st.info("👈 Create or select a website to get started")


def main():
    """Main entry point"""
    builder = WebsiteBuilder()
    builder.render()


if __name__ == "__main__":
    main()
