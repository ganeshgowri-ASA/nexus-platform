"""
Streamlit UI Module

Complete Streamlit interface for the Forms & Surveys module including form builder,
response dashboard, analytics, and settings.
"""

import streamlit as st
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from .form_builder import FormBuilder, Form, FormSettings, FormTheme
from .field_types import Field, FieldType, FieldFactory, FieldConfig
from .responses import ResponseManager, FormResponse
from .analytics import FormAnalytics, ChartGenerator
from .export import DataExporter
from .templates import TemplateLibrary, FormTemplate
from .logic import LogicRuleBuilder, ConditionOperator, ActionType, LogicOperator
from .validation import ValidationRuleBuilder


class FormsUI:
    """Main UI class for Forms & Surveys module"""

    def __init__(self):
        """Initialize the Forms UI"""
        self._init_session_state()

    def _init_session_state(self):
        """Initialize session state variables"""
        if 'form_builder' not in st.session_state:
            st.session_state.form_builder = FormBuilder()

        if 'response_manager' not in st.session_state:
            st.session_state.response_manager = ResponseManager()

        if 'current_form' not in st.session_state:
            st.session_state.current_form = None

        if 'selected_field' not in st.session_state:
            st.session_state.selected_field = None

        if 'view_mode' not in st.session_state:
            st.session_state.view_mode = 'list'  # list, builder, responses, analytics

    def render(self):
        """Render the main UI"""
        st.title("📋 Forms & Surveys")
        st.markdown("*Create beautiful forms and collect responses with powerful analytics*")

        # Sidebar navigation
        self._render_sidebar()

        # Main content based on view mode
        if st.session_state.view_mode == 'list':
            self._render_forms_list()
        elif st.session_state.view_mode == 'builder':
            self._render_form_builder()
        elif st.session_state.view_mode == 'responses':
            self._render_responses_view()
        elif st.session_state.view_mode == 'analytics':
            self._render_analytics_view()
        elif st.session_state.view_mode == 'templates':
            self._render_templates_view()

    def _render_sidebar(self):
        """Render sidebar navigation"""
        with st.sidebar:
            st.header("Navigation")

            if st.button("📝 My Forms", use_container_width=True):
                st.session_state.view_mode = 'list'
                st.rerun()

            if st.button("🎨 Templates", use_container_width=True):
                st.session_state.view_mode = 'templates'
                st.rerun()

            st.divider()

            # Current form actions
            if st.session_state.current_form:
                form = st.session_state.current_form
                st.subheader(f"Current Form")
                st.caption(form.settings.title)

                if st.button("✏️ Edit Form", use_container_width=True):
                    st.session_state.view_mode = 'builder'
                    st.rerun()

                if st.button("📊 View Responses", use_container_width=True):
                    st.session_state.view_mode = 'responses'
                    st.rerun()

                if st.button("📈 Analytics", use_container_width=True):
                    st.session_state.view_mode = 'analytics'
                    st.rerun()

                st.divider()

                # Quick stats
                responses = st.session_state.response_manager.get_form_responses(form.id)
                st.metric("Total Responses", len(responses))

                if form.status == "published":
                    st.success("✓ Published")
                else:
                    st.info("Draft")

    def _render_forms_list(self):
        """Render list of forms"""
        col1, col2 = st.columns([3, 1])

        with col1:
            st.header("My Forms")

        with col2:
            if st.button("➕ Create New Form", use_container_width=True):
                new_form = st.session_state.form_builder.create_form("Untitled Form")
                st.session_state.current_form = new_form
                st.session_state.view_mode = 'builder'
                st.rerun()

        # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            status_filter = st.selectbox(
                "Status",
                ["All", "Draft", "Published", "Closed"],
                key="status_filter"
            )

        with col2:
            search = st.text_input("🔍 Search forms", key="search_forms")

        # Get forms
        forms = st.session_state.form_builder.list_forms()

        # Apply filters
        if status_filter != "All":
            forms = [f for f in forms if f.status.lower() == status_filter.lower()]

        if search:
            forms = [f for f in forms if search.lower() in f.settings.title.lower()]

        # Display forms
        if not forms:
            st.info("No forms yet. Create your first form to get started!")
        else:
            for form in forms:
                with st.container():
                    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

                    with col1:
                        st.subheader(form.settings.title)
                        st.caption(f"Created: {form.created_at.strftime('%Y-%m-%d')}")

                    with col2:
                        responses = st.session_state.response_manager.get_form_responses(form.id)
                        st.metric("Responses", len(responses))

                    with col3:
                        if form.status == "published":
                            st.success("Published")
                        elif form.status == "closed":
                            st.error("Closed")
                        else:
                            st.info("Draft")

                    with col4:
                        if st.button("Open", key=f"open_{form.id}"):
                            st.session_state.current_form = form
                            st.session_state.view_mode = 'builder'
                            st.rerun()

                    st.divider()

    def _render_templates_view(self):
        """Render templates library"""
        st.header("📚 Form Templates")
        st.markdown("Start with a pre-built template and customize it to your needs")

        # Get all templates
        templates = TemplateLibrary.get_all_templates()

        # Category filter
        categories = list(set(t.category for t in templates))
        selected_category = st.selectbox("Filter by category", ["All"] + categories)

        if selected_category != "All":
            templates = [t for t in templates if t.category == selected_category]

        # Display templates
        cols = st.columns(2)
        for idx, template in enumerate(templates):
            with cols[idx % 2]:
                with st.container():
                    st.subheader(template.name)
                    st.caption(f"Category: {template.category}")
                    st.write(template.description)
                    st.caption(f"📋 {len(template.fields)} fields")

                    if st.button("Use Template", key=f"use_template_{idx}"):
                        # Create form from template
                        form = template.to_form()
                        st.session_state.form_builder.forms[form.id] = form
                        st.session_state.current_form = form
                        st.session_state.view_mode = 'builder'
                        st.success(f"Template '{template.name}' loaded!")
                        st.rerun()

                    st.divider()

    def _render_form_builder(self):
        """Render form builder interface"""
        if not st.session_state.current_form:
            st.warning("No form selected")
            return

        form = st.session_state.current_form

        # Top bar
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

        with col1:
            form.settings.title = st.text_input(
                "Form Title",
                value=form.settings.title,
                key="form_title"
            )

        with col2:
            if st.button("💾 Save"):
                st.success("Form saved!")

        with col3:
            if st.button("👁️ Preview"):
                self._show_form_preview(form)

        with col4:
            if form.status == "draft":
                if st.button("🚀 Publish"):
                    share_link = form.publish()
                    st.success(f"Published! Share link: {share_link}")
            else:
                if st.button("📥 Unpublish"):
                    form.unpublish()
                    st.success("Form unpublished")

        st.divider()

        # Main builder area
        tab1, tab2, tab3, tab4 = st.tabs(["📝 Build", "⚙️ Settings", "🔀 Logic", "🎨 Design"])

        with tab1:
            self._render_builder_tab(form)

        with tab2:
            self._render_settings_tab(form)

        with tab3:
            self._render_logic_tab(form)

        with tab4:
            self._render_design_tab(form)

    def _render_builder_tab(self, form: Form):
        """Render the form builder tab"""
        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader("Form Fields")

            # Form description
            form.settings.description = st.text_area(
                "Form Description",
                value=form.settings.description,
                height=100
            )

            st.divider()

            # Display existing fields
            if not form.fields:
                st.info("No fields yet. Add fields from the palette →")
            else:
                for idx, field in enumerate(form.fields):
                    with st.container():
                        col_a, col_b, col_c = st.columns([3, 1, 1])

                        with col_a:
                            st.write(f"**{field.label}**")
                            st.caption(f"Type: {field.field_type.value}")

                        with col_b:
                            if st.button("✏️ Edit", key=f"edit_{field.id}"):
                                st.session_state.selected_field = field
                                self._show_field_editor(field)

                        with col_c:
                            if st.button("🗑️", key=f"delete_{field.id}"):
                                form.remove_field(field.id)
                                st.rerun()

                        st.divider()

        with col2:
            st.subheader("Field Palette")
            st.caption("Click to add a field")

            # Field type buttons
            field_types = {
                "Short Text": FieldType.SHORT_TEXT,
                "Long Text": FieldType.LONG_TEXT,
                "Email": FieldType.EMAIL,
                "Phone": FieldType.PHONE,
                "Number": FieldType.NUMBER,
                "Dropdown": FieldType.DROPDOWN,
                "Radio Buttons": FieldType.RADIO,
                "Checkboxes": FieldType.CHECKBOX,
                "Date": FieldType.DATE,
                "Time": FieldType.TIME,
                "File Upload": FieldType.FILE_UPLOAD,
                "Rating": FieldType.RATING,
                "Scale": FieldType.SCALE,
                "NPS": FieldType.NPS,
                "Matrix": FieldType.MATRIX,
            }

            for label, field_type in field_types.items():
                if st.button(f"➕ {label}", key=f"add_{field_type.value}", use_container_width=True):
                    # Create new field
                    new_field = Field(
                        field_type=field_type,
                        label=f"New {label}",
                    )

                    # Set defaults for specific types
                    if field_type in [FieldType.DROPDOWN, FieldType.RADIO, FieldType.CHECKBOX]:
                        new_field.config.options = ["Option 1", "Option 2", "Option 3"]

                    form.add_field(new_field)
                    st.rerun()

    def _render_settings_tab(self, form: Form):
        """Render form settings tab"""
        st.subheader("Form Settings")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### Submission Settings")

            form.settings.allow_multiple_submissions = st.checkbox(
                "Allow multiple submissions",
                value=form.settings.allow_multiple_submissions
            )

            form.settings.require_login = st.checkbox(
                "Require login",
                value=form.settings.require_login
            )

            form.settings.collect_email = st.checkbox(
                "Collect email address",
                value=form.settings.collect_email
            )

            form.settings.submission_limit = st.number_input(
                "Submission limit (0 = unlimited)",
                min_value=0,
                value=form.settings.submission_limit or 0
            )

            st.markdown("### Behavior")

            form.settings.show_progress_bar = st.checkbox(
                "Show progress bar",
                value=form.settings.show_progress_bar
            )

            form.settings.auto_save = st.checkbox(
                "Auto-save responses",
                value=form.settings.auto_save
            )

        with col2:
            st.markdown("### Notifications")

            form.settings.send_confirmation_email = st.checkbox(
                "Send confirmation email to respondent",
                value=form.settings.send_confirmation_email
            )

            notification_emails = st.text_area(
                "Notification emails (one per line)",
                value="\n".join(form.settings.notification_emails)
            )
            form.settings.notification_emails = [
                e.strip() for e in notification_emails.split("\n") if e.strip()
            ]

            st.markdown("### Messages")

            form.settings.success_message = st.text_area(
                "Success message",
                value=form.settings.success_message,
                height=100
            )

            form.settings.redirect_url = st.text_input(
                "Redirect URL (after submission)",
                value=form.settings.redirect_url or ""
            )

    def _render_logic_tab(self, form: Form):
        """Render conditional logic tab"""
        st.subheader("Conditional Logic")
        st.markdown("Create rules to show/hide fields based on user responses")

        # Display existing rules
        if form.logic.rules:
            st.markdown("### Existing Rules")
            for rule_id, rule in form.logic.rules.items():
                with st.expander(f"📋 {rule.name or 'Untitled Rule'}"):
                    st.write(f"**Conditions ({rule.logic_operator.value.upper()}):**")
                    for condition in rule.conditions:
                        field = form.get_field(condition.field_id)
                        field_label = field.label if field else condition.field_id
                        st.write(f"- {field_label} {condition.operator.value} {condition.value}")

                    st.write("**Actions:**")
                    for action in rule.actions:
                        st.write(f"- {action.action_type.value} → {action.target_id}")

                    if st.button("Delete Rule", key=f"delete_rule_{rule_id}"):
                        form.logic.remove_rule(rule_id)
                        st.rerun()
        else:
            st.info("No logic rules yet")

        st.divider()

        # Add new rule
        with st.expander("➕ Add New Logic Rule"):
            rule_name = st.text_input("Rule Name", key="new_rule_name")

            st.markdown("**When this condition is met:**")

            col1, col2, col3 = st.columns(3)
            with col1:
                trigger_field = st.selectbox(
                    "Field",
                    options=[f.id for f in form.fields],
                    format_func=lambda x: next((f.label for f in form.fields if f.id == x), x),
                    key="trigger_field"
                )

            with col2:
                operator = st.selectbox(
                    "Operator",
                    options=[op.value for op in ConditionOperator],
                    key="operator"
                )

            with col3:
                trigger_value = st.text_input("Value", key="trigger_value")

            st.markdown("**Perform this action:**")

            col1, col2 = st.columns(2)
            with col1:
                action_type = st.selectbox(
                    "Action",
                    options=[ActionType.SHOW_FIELD.value, ActionType.HIDE_FIELD.value,
                            ActionType.REQUIRE_FIELD.value, ActionType.UNREQUIRE_FIELD.value],
                    key="action_type"
                )

            with col2:
                target_field = st.selectbox(
                    "Target Field",
                    options=[f.id for f in form.fields],
                    format_func=lambda x: next((f.label for f in form.fields if f.id == x), x),
                    key="target_field"
                )

            if st.button("Add Rule"):
                # Create and add the rule
                rule = LogicRuleBuilder(rule_name) \
                    .add_condition(trigger_field, ConditionOperator(operator), trigger_value) \
                    .add_action(ActionType(action_type), target_field) \
                    .build()

                form.logic.add_rule(rule)
                st.success("Rule added!")
                st.rerun()

    def _render_design_tab(self, form: Form):
        """Render form design tab"""
        st.subheader("Form Design")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### Theme")

            theme_options = list(FormTheme.THEMES.keys())
            selected_theme = st.selectbox(
                "Select Theme",
                options=theme_options,
                index=theme_options.index(form.settings.theme) if form.settings.theme in theme_options else 0
            )

            if st.button("Apply Theme"):
                FormTheme.apply_theme(form, selected_theme)
                st.success(f"Theme '{selected_theme}' applied!")

            st.markdown("### Colors")

            form.settings.primary_color = st.color_picker(
                "Primary Color",
                value=form.settings.primary_color
            )

            form.settings.background_color = st.color_picker(
                "Background Color",
                value=form.settings.background_color
            )

        with col2:
            st.markdown("### Branding")

            form.settings.logo_url = st.text_input(
                "Logo URL",
                value=form.settings.logo_url or ""
            )

            if form.settings.logo_url:
                st.image(form.settings.logo_url, width=200)

            st.markdown("### Custom CSS")

            form.settings.custom_css = st.text_area(
                "Custom CSS",
                value=form.settings.custom_css,
                height=200,
                placeholder=".form-field { margin: 10px; }"
            )

    def _render_responses_view(self):
        """Render responses view"""
        if not st.session_state.current_form:
            st.warning("No form selected")
            return

        form = st.session_state.current_form
        responses = st.session_state.response_manager.get_form_responses(form.id)

        st.header(f"📊 Responses: {form.settings.title}")

        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Responses", len(responses))

        with col2:
            complete_count = len([r for r in responses if r.is_complete])
            st.metric("Complete", complete_count)

        with col3:
            if responses:
                avg_time = sum(r.time_spent for r in responses) / len(responses)
                st.metric("Avg Time", f"{avg_time:.0f}s")
            else:
                st.metric("Avg Time", "0s")

        with col4:
            # Export button
            if st.button("📥 Export"):
                self._show_export_dialog(form, responses)

        st.divider()

        # Tabs for different views
        tab1, tab2, tab3 = st.tabs(["📋 Individual", "📊 Summary", "🔍 Filter"])

        with tab1:
            self._render_individual_responses(form, responses)

        with tab2:
            self._render_summary_responses(form, responses)

        with tab3:
            self._render_filtered_responses(form, responses)

    def _render_individual_responses(self, form: Form, responses: List[FormResponse]):
        """Render individual responses"""
        if not responses:
            st.info("No responses yet")
            return

        # Pagination
        page_size = 10
        total_pages = (len(responses) - 1) // page_size + 1

        page = st.number_input("Page", min_value=1, max_value=total_pages, value=1) - 1

        start_idx = page * page_size
        end_idx = start_idx + page_size
        page_responses = responses[start_idx:end_idx]

        # Display responses
        for response in page_responses:
            with st.expander(
                f"Response {response.id[:8]} - {response.submitted_at.strftime('%Y-%m-%d %H:%M')}"
            ):
                # Metadata
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.caption(f"Submitted: {response.submitted_at.strftime('%Y-%m-%d %H:%M:%S')}")
                with col2:
                    st.caption(f"Time Spent: {response.time_spent}s")
                with col3:
                    if response.respondent_email:
                        st.caption(f"Email: {response.respondent_email}")

                st.divider()

                # Response data
                for field in form.fields:
                    value = response.data.get(field.id, "")
                    if isinstance(value, list):
                        value = ", ".join(str(v) for v in value)

                    st.write(f"**{field.label}:**")
                    st.write(value or "*No answer*")

                # Actions
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Mark as Spam", key=f"spam_{response.id}"):
                        st.session_state.response_manager.mark_as_spam(response.id)
                        st.success("Marked as spam")
                        st.rerun()

                with col2:
                    if st.button("Delete", key=f"del_{response.id}"):
                        st.session_state.response_manager.delete_response(response.id)
                        st.success("Response deleted")
                        st.rerun()

    def _render_summary_responses(self, form: Form, responses: List[FormResponse]):
        """Render summary of responses"""
        if not responses:
            st.info("No responses yet")
            return

        # Get spreadsheet view
        spreadsheet_data = st.session_state.response_manager.get_spreadsheet_view(form.id)

        # Display as dataframe
        df = pd.DataFrame(spreadsheet_data["rows"], columns=spreadsheet_data["headers"])
        st.dataframe(df, use_container_width=True)

    def _render_filtered_responses(self, form: Form, responses: List[FormResponse]):
        """Render filtered responses"""
        st.subheader("Filter Responses")

        # Date range filter
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("From Date", value=datetime.now() - timedelta(days=30))
        with col2:
            end_date = st.date_input("To Date", value=datetime.now())

        # Field filters
        st.markdown("### Filter by Field Values")

        selected_field = st.selectbox(
            "Select Field",
            options=[f.id for f in form.fields],
            format_func=lambda x: next((f.label for f in form.fields if f.id == x), x)
        )

        filter_value = st.text_input("Filter Value")

        if st.button("Apply Filters"):
            # Apply date filter
            filtered = st.session_state.response_manager.get_responses_by_date_range(
                form.id,
                datetime.combine(start_date, datetime.min.time()),
                datetime.combine(end_date, datetime.max.time())
            )

            # Apply field filter
            if filter_value:
                filtered = [
                    r for r in filtered
                    if str(r.data.get(selected_field, "")).lower() == filter_value.lower()
                ]

            st.success(f"Found {len(filtered)} matching responses")

            # Display filtered results
            for response in filtered[:10]:
                st.write(f"Response {response.id[:8]} - {response.submitted_at}")

    def _render_analytics_view(self):
        """Render analytics view"""
        if not st.session_state.current_form:
            st.warning("No form selected")
            return

        form = st.session_state.current_form
        responses = st.session_state.response_manager.get_form_responses(form.id)

        if not responses:
            st.info("No responses yet. Analytics will appear once you receive responses.")
            return

        analytics = FormAnalytics(responses, form.fields)

        st.header(f"📈 Analytics: {form.settings.title}")

        # Overview metrics
        metrics = analytics.get_overview_metrics()

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Submissions", metrics.total_submissions)
        with col2:
            st.metric("Completion Rate", f"{metrics.completion_rate:.1f}%")
        with col3:
            st.metric("Avg. Time", f"{metrics.average_time / 60:.1f} min")
        with col4:
            st.metric("Drop-off Rate", f"{metrics.abandonment_rate:.1f}%")

        st.divider()

        # Tabs for different analytics
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "📉 Trends", "🎯 Fields", "⏱️ Time"])

        with tab1:
            self._render_overview_analytics(analytics)

        with tab2:
            self._render_trends_analytics(analytics)

        with tab3:
            self._render_field_analytics(analytics, form)

        with tab4:
            self._render_time_analytics(analytics)

    def _render_overview_analytics(self, analytics: FormAnalytics):
        """Render overview analytics"""
        st.subheader("Response Overview")

        # Device distribution
        device_data = analytics.get_device_distribution()
        fig = px.pie(
            values=list(device_data.values()),
            names=list(device_data.keys()),
            title="Responses by Device"
        )
        st.plotly_chart(fig, use_container_width=True)

        # Day of week distribution
        daily_data = analytics.get_daily_distribution()
        fig = px.bar(
            x=list(daily_data.keys()),
            y=list(daily_data.values()),
            title="Responses by Day of Week",
            labels={"x": "Day", "y": "Count"}
        )
        st.plotly_chart(fig, use_container_width=True)

    def _render_trends_analytics(self, analytics: FormAnalytics):
        """Render trends analytics"""
        st.subheader("Response Trends")

        # Response trend over time
        days = st.slider("Days to show", 7, 90, 30)
        trends = analytics.get_response_trends(days=days)

        fig = px.line(
            x=list(trends.keys()),
            y=list(trends.values()),
            title=f"Responses Over Last {days} Days",
            labels={"x": "Date", "y": "Responses"}
        )
        st.plotly_chart(fig, use_container_width=True)

        # Hourly distribution
        hourly = analytics.get_hourly_distribution()
        fig = px.bar(
            x=list(hourly.keys()),
            y=list(hourly.values()),
            title="Responses by Hour of Day",
            labels={"x": "Hour", "y": "Count"}
        )
        st.plotly_chart(fig, use_container_width=True)

    def _render_field_analytics(self, analytics: FormAnalytics, form: Form):
        """Render field-specific analytics"""
        st.subheader("Field Statistics")

        # Select field
        selected_field = st.selectbox(
            "Select Field to Analyze",
            options=[f.id for f in form.fields],
            format_func=lambda x: next((f.label for f in form.fields if f.id == x), x)
        )

        field = form.get_field(selected_field)
        if not field:
            return

        stats = analytics.get_field_statistics(selected_field)

        # Display stats
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Responses", stats["total_responses"])
        with col2:
            st.metric("Filled", stats["filled_count"])
        with col3:
            st.metric("Empty", stats["empty_count"])

        # Type-specific visualizations
        if "option_counts" in stats:
            # For choice fields, show distribution
            fig = px.bar(
                x=list(stats["option_counts"].keys()),
                y=list(stats["option_counts"].values()),
                title=f"Response Distribution: {field.label}",
                labels={"x": "Option", "y": "Count"}
            )
            st.plotly_chart(fig, use_container_width=True)

        elif "average" in stats:
            # For numeric fields, show statistics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Average", f"{stats['average']:.2f}")
            with col2:
                st.metric("Min", stats["min"])
            with col3:
                st.metric("Max", stats["max"])

    def _render_time_analytics(self, analytics: FormAnalytics):
        """Render time-based analytics"""
        st.subheader("Time Analysis")

        # Completion time distribution
        time_dist = analytics.get_time_distribution()

        fig = px.bar(
            x=list(time_dist.keys()),
            y=list(time_dist.values()),
            title="Completion Time Distribution",
            labels={"x": "Time Range", "y": "Count"}
        )
        st.plotly_chart(fig, use_container_width=True)

        # Drop-off analysis
        drop_offs = analytics.get_drop_off_analysis()

        drop_off_data = [
            {
                "Field": data["field_label"],
                "Position": data["position"],
                "Completion Rate": data["completion_rate"],
                "Drop-off Rate": data["drop_off_rate"]
            }
            for data in drop_offs.values()
        ]

        df = pd.DataFrame(drop_off_data)
        df = df.sort_values("Position")

        fig = px.line(
            df,
            x="Position",
            y="Completion Rate",
            title="Field Completion Rate by Position",
            markers=True
        )
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(df, use_container_width=True)

    def _show_form_preview(self, form: Form):
        """Show form preview in modal"""
        with st.expander("👁️ Form Preview", expanded=True):
            st.markdown(f"# {form.settings.title}")
            if form.settings.description:
                st.markdown(form.settings.description)

            st.divider()

            for field in form.fields:
                self._render_field_preview(field)

            st.button("Submit", disabled=True)

    def _render_field_preview(self, field: Field):
        """Render a field in preview mode"""
        label = field.label
        if field.config.required:
            label += " *"

        if field.description:
            st.caption(field.description)

        if field.field_type == FieldType.SHORT_TEXT:
            st.text_input(label, key=f"preview_{field.id}", disabled=True)

        elif field.field_type == FieldType.LONG_TEXT:
            st.text_area(label, key=f"preview_{field.id}", disabled=True)

        elif field.field_type == FieldType.EMAIL:
            st.text_input(label, key=f"preview_{field.id}", disabled=True, placeholder="email@example.com")

        elif field.field_type == FieldType.DROPDOWN:
            st.selectbox(label, options=field.config.options or [], key=f"preview_{field.id}", disabled=True)

        elif field.field_type == FieldType.RADIO:
            st.radio(label, options=field.config.options or [], key=f"preview_{field.id}", disabled=True)

        elif field.field_type == FieldType.CHECKBOX:
            for option in field.config.options or []:
                st.checkbox(option, key=f"preview_{field.id}_{option}", disabled=True)

        elif field.field_type == FieldType.RATING:
            st.slider(label, 1, field.config.max_rating, key=f"preview_{field.id}", disabled=True)

    def _show_field_editor(self, field: Field):
        """Show field editor dialog"""
        with st.expander(f"✏️ Edit: {field.label}", expanded=True):
            field.label = st.text_input("Field Label", value=field.label, key=f"edit_label_{field.id}")
            field.description = st.text_area("Description", value=field.description or "", key=f"edit_desc_{field.id}")

            field.config.required = st.checkbox("Required", value=field.config.required, key=f"edit_req_{field.id}")

            # Type-specific options
            if field.field_type in [FieldType.DROPDOWN, FieldType.RADIO, FieldType.CHECKBOX]:
                options_text = st.text_area(
                    "Options (one per line)",
                    value="\n".join(field.config.options or []),
                    key=f"edit_opts_{field.id}"
                )
                field.config.options = [opt.strip() for opt in options_text.split("\n") if opt.strip()]

            if st.button("Save Changes", key=f"save_{field.id}"):
                st.success("Field updated!")
                st.session_state.selected_field = None
                st.rerun()

    def _show_export_dialog(self, form: Form, responses: List[FormResponse]):
        """Show export dialog"""
        with st.expander("📥 Export Responses", expanded=True):
            export_format = st.selectbox("Format", ["CSV", "JSON", "Excel"])

            if st.button("Export"):
                exporter = DataExporter(responses, form.fields)

                if export_format == "CSV":
                    csv_content = exporter.export_to_csv()
                    st.download_button(
                        "Download CSV",
                        csv_content,
                        f"form_responses_{form.id}.csv",
                        "text/csv"
                    )

                elif export_format == "JSON":
                    json_content = exporter.export_to_json()
                    st.download_button(
                        "Download JSON",
                        json_content,
                        f"form_responses_{form.id}.json",
                        "application/json"
                    )

                elif export_format == "Excel":
                    st.info("Excel export requires file system access")


def main():
    """Main entry point"""
    st.set_page_config(
        page_title="NEXUS Forms & Surveys",
        page_icon="📋",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Custom CSS
    st.markdown("""
        <style>
        .stButton button {
            width: 100%;
        }
        </style>
    """, unsafe_allow_html=True)

    ui = FormsUI()
    ui.render()


if __name__ == "__main__":
    main()
