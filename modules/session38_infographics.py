"""
Session 38: Infographics Designer
Features: Templates, icons, charts, AI-powered design
"""
import streamlit as st
import json
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from typing import Dict, List, Any
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from utils.ai_assistant import ai_assistant
from utils.storage import storage
import pandas as pd


class InfographicsDesigner:
    """Infographics Designer with templates, icons, and charts"""

    def __init__(self):
        """Initialize infographics designer"""
        if 'infographics' not in st.session_state:
            st.session_state.infographics = self.load_infographics()
        if 'current_infographic' not in st.session_state:
            st.session_state.current_infographic = None

    def load_infographics(self) -> List[Dict]:
        """Load saved infographics"""
        infographics = []
        files = storage.list_files('infographics', '.json')
        for file in files:
            data = storage.load_json(file, 'infographics')
            if data:
                infographics.append(data)
        return infographics

    def save_infographic(self, infographic: Dict) -> bool:
        """Save infographic"""
        filename = f"infographic_{infographic['id']}.json"
        return storage.save_json(filename, infographic, 'infographics')

    def templates(self) -> Dict[str, Dict]:
        """Available templates"""
        return {
            'Statistics': {
                'description': 'Display key statistics and metrics',
                'sections': ['header', 'stats_grid', 'chart', 'footer']
            },
            'Timeline': {
                'description': 'Show events chronologically',
                'sections': ['header', 'timeline', 'footer']
            },
            'Comparison': {
                'description': 'Compare multiple items or options',
                'sections': ['header', 'comparison_table', 'charts', 'footer']
            },
            'Process': {
                'description': 'Illustrate a step-by-step process',
                'sections': ['header', 'steps', 'icons', 'footer']
            },
            'Hierarchy': {
                'description': 'Show organizational structure',
                'sections': ['header', 'org_chart', 'footer']
            }
        }

    def icons(self) -> List[str]:
        """Available icon categories"""
        return [
            '📊 Charts & Data',
            '👥 People & Teams',
            '💼 Business',
            '🎯 Goals & Targets',
            '⚙️ Technology',
            '🌍 Global',
            '💡 Ideas',
            '📈 Growth',
            '🔒 Security',
            '⏰ Time'
        ]

    def create_infographic(self, name: str, template: str) -> Dict:
        """Create new infographic"""
        template_data = self.templates()[template]
        infographic = {
            'id': datetime.now().strftime('%Y%m%d_%H%M%S'),
            'name': name,
            'template': template,
            'created': datetime.now().isoformat(),
            'modified': datetime.now().isoformat(),
            'sections': template_data['sections'],
            'data': {},
            'charts': [],
            'style': {
                'color_scheme': 'blue',
                'font': 'Arial',
                'background': 'white'
            }
        }
        return infographic

    def render(self):
        """Render infographics designer"""
        st.title("📊 Infographics Designer")
        st.markdown("*Create stunning infographics with templates, icons, and charts*")

        # Sidebar
        with st.sidebar:
            st.header("Infographics Manager")

            # New infographic
            with st.expander("➕ New Infographic", expanded=False):
                new_name = st.text_input("Infographic Name", key="new_infographic_name")
                template = st.selectbox(
                    "Template",
                    options=list(self.templates().keys()),
                    format_func=lambda x: f"{x} - {self.templates()[x]['description']}"
                )

                if st.button("Create Infographic", type="primary"):
                    if new_name:
                        infographic = self.create_infographic(new_name, template)
                        st.session_state.infographics.append(infographic)
                        st.session_state.current_infographic = infographic
                        self.save_infographic(infographic)
                        st.success(f"Created '{new_name}'")
                        st.rerun()

            # Existing infographics
            if st.session_state.infographics:
                st.subheader("Saved Infographics")
                for infographic in st.session_state.infographics:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        if st.button(infographic['name'], key=f"load_{infographic['id']}"):
                            st.session_state.current_infographic = infographic
                            st.rerun()
                    with col2:
                        if st.button("🗑️", key=f"del_{infographic['id']}"):
                            storage.delete_file(f"infographic_{infographic['id']}.json", 'infographics')
                            st.session_state.infographics.remove(infographic)
                            st.rerun()

        # Main designer
        if st.session_state.current_infographic:
            infographic = st.session_state.current_infographic

            tabs = st.tabs(["🎨 Design", "📊 Data & Charts", "🎭 Style", "🤖 AI Assistant", "👁️ Preview"])

            # Design Tab
            with tabs[0]:
                st.subheader(f"Designing: {infographic['name']}")
                st.caption(f"Template: {infographic['template']}")

                # Section editor
                for section in infographic['sections']:
                    with st.expander(f"📝 {section.replace('_', ' ').title()}", expanded=True):
                        if section == 'header':
                            title = st.text_input("Title", value=infographic['data'].get('title', ''), key=f"{section}_title")
                            subtitle = st.text_input("Subtitle", value=infographic['data'].get('subtitle', ''), key=f"{section}_subtitle")
                            infographic['data']['title'] = title
                            infographic['data']['subtitle'] = subtitle

                        elif section == 'stats_grid':
                            num_stats = st.number_input("Number of Statistics", 1, 6, 4, key=f"{section}_num")
                            if 'stats' not in infographic['data']:
                                infographic['data']['stats'] = []

                            for i in range(int(num_stats)):
                                col1, col2 = st.columns(2)
                                with col1:
                                    label = st.text_input(f"Stat {i+1} Label", key=f"stat_{i}_label")
                                with col2:
                                    value = st.text_input(f"Stat {i+1} Value", key=f"stat_{i}_value")

                                if i < len(infographic['data']['stats']):
                                    infographic['data']['stats'][i] = {'label': label, 'value': value}
                                else:
                                    infographic['data']['stats'].append({'label': label, 'value': value})

                        elif section == 'timeline':
                            num_events = st.number_input("Number of Events", 1, 10, 5, key=f"{section}_num")
                            if 'timeline' not in infographic['data']:
                                infographic['data']['timeline'] = []

                            for i in range(int(num_events)):
                                col1, col2 = st.columns([1, 3])
                                with col1:
                                    date = st.text_input(f"Date {i+1}", key=f"event_{i}_date")
                                with col2:
                                    event = st.text_input(f"Event {i+1}", key=f"event_{i}_text")

                                if i < len(infographic['data']['timeline']):
                                    infographic['data']['timeline'][i] = {'date': date, 'event': event}
                                else:
                                    infographic['data']['timeline'].append({'date': date, 'event': event})

                        elif section == 'steps':
                            num_steps = st.number_input("Number of Steps", 1, 8, 4, key=f"{section}_num")
                            if 'steps' not in infographic['data']:
                                infographic['data']['steps'] = []

                            for i in range(int(num_steps)):
                                step_text = st.text_area(f"Step {i+1}", key=f"step_{i}_text", height=80)
                                if i < len(infographic['data']['steps']):
                                    infographic['data']['steps'][i] = step_text
                                else:
                                    infographic['data']['steps'].append(step_text)

                        elif section == 'footer':
                            footer = st.text_area("Footer Text", value=infographic['data'].get('footer', ''), key=f"{section}_text")
                            infographic['data']['footer'] = footer

                if st.button("💾 Save Design", type="primary"):
                    infographic['modified'] = datetime.now().isoformat()
                    self.save_infographic(infographic)
                    st.success("Design saved!")

            # Data & Charts Tab
            with tabs[1]:
                st.subheader("📊 Add Charts")

                chart_type = st.selectbox(
                    "Chart Type",
                    ["Bar Chart", "Line Chart", "Pie Chart", "Scatter Plot", "Funnel", "Gauge"]
                )

                chart_title = st.text_input("Chart Title")

                # Data input
                st.markdown("**Chart Data**")
                data_input_method = st.radio("Input Method", ["Manual", "CSV Data"])

                chart_data = None

                if data_input_method == "Manual":
                    col1, col2 = st.columns(2)
                    with col1:
                        labels = st.text_area("Labels (one per line)", height=100)
                    with col2:
                        values = st.text_area("Values (one per line)", height=100)

                    if labels and values:
                        labels_list = [l.strip() for l in labels.split('\n') if l.strip()]
                        values_list = [float(v.strip()) for v in values.split('\n') if v.strip()]

                        if len(labels_list) == len(values_list):
                            chart_data = pd.DataFrame({
                                'Label': labels_list,
                                'Value': values_list
                            })

                else:
                    csv_data = st.text_area("Paste CSV Data", height=150)
                    if csv_data:
                        try:
                            from io import StringIO
                            chart_data = pd.read_csv(StringIO(csv_data))
                        except:
                            st.error("Invalid CSV data")

                # Preview and add chart
                if chart_data is not None and not chart_data.empty:
                    st.markdown("**Preview**")

                    # Create chart based on type
                    fig = None
                    if chart_type == "Bar Chart":
                        fig = px.bar(chart_data, x=chart_data.columns[0], y=chart_data.columns[1], title=chart_title)
                    elif chart_type == "Line Chart":
                        fig = px.line(chart_data, x=chart_data.columns[0], y=chart_data.columns[1], title=chart_title)
                    elif chart_type == "Pie Chart":
                        fig = px.pie(chart_data, names=chart_data.columns[0], values=chart_data.columns[1], title=chart_title)
                    elif chart_type == "Scatter Plot":
                        fig = px.scatter(chart_data, x=chart_data.columns[0], y=chart_data.columns[1], title=chart_title)
                    elif chart_type == "Funnel":
                        fig = go.Figure(go.Funnel(
                            y=chart_data[chart_data.columns[0]],
                            x=chart_data[chart_data.columns[1]],
                            textinfo="value+percent initial"
                        ))
                        fig.update_layout(title=chart_title)
                    elif chart_type == "Gauge":
                        value = chart_data.iloc[0, 1] if len(chart_data) > 0 else 0
                        fig = go.Figure(go.Indicator(
                            mode="gauge+number",
                            value=value,
                            title={'text': chart_title},
                            gauge={'axis': {'range': [None, 100]}}
                        ))

                    if fig:
                        st.plotly_chart(fig, use_container_width=True)

                        if st.button("➕ Add Chart to Infographic"):
                            chart_config = {
                                'type': chart_type,
                                'title': chart_title,
                                'data': chart_data.to_dict(),
                                'id': f"chart_{len(infographic['charts'])}"
                            }
                            infographic['charts'].append(chart_config)
                            self.save_infographic(infographic)
                            st.success("Chart added!")
                            st.rerun()

                # Display existing charts
                if infographic['charts']:
                    st.markdown("### Existing Charts")
                    for idx, chart in enumerate(infographic['charts']):
                        col1, col2 = st.columns([4, 1])
                        with col1:
                            st.write(f"**{chart['title']}** ({chart['type']})")
                        with col2:
                            if st.button("🗑️", key=f"del_chart_{idx}"):
                                infographic['charts'].pop(idx)
                                self.save_infographic(infographic)
                                st.rerun()

            # Style Tab
            with tabs[2]:
                st.subheader("🎭 Style Your Infographic")

                col1, col2 = st.columns(2)

                with col1:
                    color_scheme = st.selectbox(
                        "Color Scheme",
                        ["blue", "green", "red", "purple", "orange", "teal", "pink"],
                        index=["blue", "green", "red", "purple", "orange", "teal", "pink"].index(
                            infographic['style'].get('color_scheme', 'blue')
                        )
                    )
                    infographic['style']['color_scheme'] = color_scheme

                    font = st.selectbox(
                        "Font Family",
                        ["Arial", "Helvetica", "Georgia", "Times New Roman", "Courier", "Verdana"],
                        index=["Arial", "Helvetica", "Georgia", "Times New Roman", "Courier", "Verdana"].index(
                            infographic['style'].get('font', 'Arial')
                        )
                    )
                    infographic['style']['font'] = font

                with col2:
                    background = st.selectbox(
                        "Background",
                        ["white", "light gray", "gradient", "dark"],
                        index=["white", "light gray", "gradient", "dark"].index(
                            infographic['style'].get('background', 'white')
                        )
                    )
                    infographic['style']['background'] = background

                # Icons
                st.markdown("### 🎭 Icons Library")
                selected_icons = st.multiselect("Select Icon Categories", self.icons())

                if st.button("💾 Save Style"):
                    infographic['modified'] = datetime.now().isoformat()
                    self.save_infographic(infographic)
                    st.success("Style saved!")

            # AI Assistant Tab
            with tabs[3]:
                st.subheader("🤖 AI-Powered Design Assistance")

                ai_task = st.radio(
                    "What would you like AI to help with?",
                    ["Suggest Layout", "Generate Content", "Improve Design", "Create Data Story"]
                )

                if ai_task == "Suggest Layout":
                    data_type = st.text_input("What type of data are you visualizing?")
                    purpose = st.text_area("What's the purpose of this infographic?")

                    if st.button("Get Layout Suggestions"):
                        if data_type and purpose:
                            with st.spinner("Analyzing and suggesting..."):
                                suggestions = ai_assistant.suggest_infographic_layout(data_type, purpose)
                                st.markdown(suggestions)

                elif ai_task == "Generate Content":
                    topic = st.text_input("Topic")
                    num_points = st.slider("Number of key points", 3, 10, 5)

                    if st.button("Generate Content"):
                        if topic:
                            with st.spinner("Generating content..."):
                                prompt = f"Generate {num_points} key points and statistics for an infographic about: {topic}"
                                content = ai_assistant.generate(prompt, max_tokens=1000)
                                st.markdown(content)

                elif ai_task == "Improve Design":
                    current_design = json.dumps(infographic['data'], indent=2)
                    st.text_area("Current Design", current_design, height=200, disabled=True)

                    if st.button("Get Design Improvements"):
                        with st.spinner("Analyzing design..."):
                            prompt = f"Suggest improvements for this infographic design:\n{current_design}"
                            improvements = ai_assistant.generate(prompt, max_tokens=1000)
                            st.markdown(improvements)

                else:  # Create Data Story
                    if st.button("Generate Data Story"):
                        with st.spinner("Creating narrative..."):
                            data_summary = json.dumps(infographic['data'], indent=2)
                            prompt = f"Create a compelling narrative story from this infographic data:\n{data_summary}"
                            story = ai_assistant.generate(prompt, max_tokens=1500)
                            st.markdown(story)

            # Preview Tab
            with tabs[4]:
                st.subheader("👁️ Preview")

                # Display infographic
                if 'title' in infographic['data']:
                    st.title(infographic['data']['title'])
                    if 'subtitle' in infographic['data']:
                        st.subheader(infographic['data']['subtitle'])

                # Stats grid
                if 'stats' in infographic['data'] and infographic['data']['stats']:
                    st.markdown("---")
                    cols = st.columns(len(infographic['data']['stats']))
                    for idx, stat in enumerate(infographic['data']['stats']):
                        with cols[idx]:
                            st.metric(stat.get('label', ''), stat.get('value', ''))

                # Timeline
                if 'timeline' in infographic['data'] and infographic['data']['timeline']:
                    st.markdown("---")
                    st.markdown("### Timeline")
                    for event in infographic['data']['timeline']:
                        st.markdown(f"**{event.get('date', '')}** - {event.get('event', '')}")

                # Steps
                if 'steps' in infographic['data'] and infographic['data']['steps']:
                    st.markdown("---")
                    st.markdown("### Process Steps")
                    for idx, step in enumerate(infographic['data']['steps']):
                        st.markdown(f"**Step {idx + 1}:** {step}")

                # Charts
                if infographic['charts']:
                    st.markdown("---")
                    for chart in infographic['charts']:
                        try:
                            chart_data = pd.DataFrame(chart['data'])
                            if chart['type'] == "Bar Chart":
                                fig = px.bar(chart_data, x=chart_data.columns[0], y=chart_data.columns[1], title=chart['title'])
                            elif chart['type'] == "Pie Chart":
                                fig = px.pie(chart_data, names=chart_data.columns[0], values=chart_data.columns[1], title=chart['title'])
                            # Add other chart types as needed
                            else:
                                fig = px.bar(chart_data, x=chart_data.columns[0], y=chart_data.columns[1], title=chart['title'])

                            st.plotly_chart(fig, use_container_width=True)
                        except:
                            st.write(f"Chart: {chart['title']}")

                # Footer
                if 'footer' in infographic['data']:
                    st.markdown("---")
                    st.caption(infographic['data']['footer'])

                # Export
                st.markdown("---")
                if st.button("📥 Download as JSON"):
                    st.download_button(
                        "Download",
                        json.dumps(infographic, indent=2),
                        file_name=f"{infographic['name']}.json",
                        mime="application/json"
                    )

        else:
            st.info("👈 Create or select an infographic to get started")

            # Welcome message
            st.markdown("""
            ## Welcome to Infographics Designer! 📊

            **Features:**
            - 🎨 Professional templates
            - 📊 Interactive charts and graphs
            - 🎭 Icon library
            - 🤖 AI-powered design assistance
            - 👁️ Live preview

            **Get Started:**
            1. Choose a template from the sidebar
            2. Add your data and content
            3. Customize charts and visuals
            4. Use AI for design suggestions
            5. Export your infographic
            """)


def main():
    """Main entry point"""
    designer = InfographicsDesigner()
    designer.render()


if __name__ == "__main__":
    main()
