"""
Visual Bot Builder page
"""
import streamlit as st
import requests
import json

API_URL = "http://localhost:8000"


def show():
    """Display the bot builder page"""
    st.markdown('<p class="main-header">🛠️ Visual Bot Builder</p>', unsafe_allow_html=True)

    # Tabs for different sections
    tab1, tab2, tab3 = st.tabs(["Create Automation", "Workflow Editor", "Test & Deploy"])

    with tab1:
        show_create_automation()

    with tab2:
        show_workflow_editor()

    with tab3:
        show_test_deploy()


def show_create_automation():
    """Show automation creation form"""
    st.markdown("### Create New Automation")

    with st.form("create_automation_form"):
        name = st.text_input("Automation Name*", placeholder="e.g., Daily Report Generator")
        description = st.text_area(
            "Description", placeholder="Describe what this automation does..."
        )

        col1, col2 = st.columns(2)

        with col1:
            trigger_type = st.selectbox(
                "Trigger Type", ["manual", "scheduled", "webhook", "event"]
            )

        with col2:
            timeout = st.number_input("Timeout (seconds)", min_value=60, value=3600)

        # Bot selection
        try:
            bots_response = requests.get(f"{API_URL}/api/v1/rpa/bots?status=active")
            if bots_response.status_code == 200:
                bots = bots_response.json()
                bot_options = {bot["name"]: bot["id"] for bot in bots}
                bot_options["None"] = None

                selected_bot = st.selectbox("Assign to Bot", list(bot_options.keys()))
                bot_id = bot_options[selected_bot]
        except Exception:
            bot_id = None
            st.warning("Could not load bots")

        tags = st.text_input("Tags (comma-separated)", placeholder="reporting, daily, automated")

        submitted = st.form_submit_button("Create Automation")

        if submitted:
            if not name:
                st.error("Automation name is required")
            else:
                # Parse tags
                tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]

                # Create automation
                automation_data = {
                    "name": name,
                    "description": description,
                    "bot_id": bot_id,
                    "trigger_type": trigger_type,
                    "workflow": {"nodes": [], "edges": [], "variables": {}},
                    "timeout": timeout,
                    "tags": tag_list,
                    "created_by": st.session_state.current_user,
                }

                try:
                    response = requests.post(
                        f"{API_URL}/api/v1/rpa/automations",
                        json=automation_data,
                    )

                    if response.status_code == 200:
                        st.success(f"Automation '{name}' created successfully!")
                        st.session_state.current_automation = response.json()
                    else:
                        st.error(f"Failed to create automation: {response.json()}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")


def show_workflow_editor():
    """Show workflow editor"""
    st.markdown("### Workflow Editor")

    if "current_automation" not in st.session_state:
        st.info("Please create an automation first or select an existing one")

        # Load existing automations
        try:
            response = requests.get(f"{API_URL}/api/v1/rpa/automations?limit=50")
            if response.status_code == 200:
                automations = response.json()
                if automations:
                    automation_options = {a["name"]: a for a in automations}
                    selected = st.selectbox(
                        "Select Automation", list(automation_options.keys())
                    )

                    if st.button("Load"):
                        st.session_state.current_automation = automation_options[
                            selected
                        ]
                        st.rerun()
        except Exception as e:
            st.error(f"Failed to load automations: {str(e)}")

        return

    automation = st.session_state.current_automation

    st.markdown(f"**Editing:** {automation['name']}")

    # Initialize workflow if not present
    if "workflow" not in automation or not automation["workflow"]:
        automation["workflow"] = {"nodes": [], "edges": [], "variables": {}}

    # Action types
    action_types = {
        "Click": "click",
        "Type Text": "type",
        "Wait": "wait",
        "Condition": "condition",
        "Loop": "loop",
        "Set Variable": "set_variable",
        "HTTP Request": "http_request",
        "Screenshot": "screenshot",
        "Log Message": "log",
    }

    # Add node section
    st.markdown("#### Add Action Node")

    col1, col2 = st.columns([1, 3])

    with col1:
        selected_action = st.selectbox("Action Type", list(action_types.keys()))

    with col2:
        node_name = st.text_input("Action Name", value=f"{selected_action} Action")

    # Action-specific configuration
    config = {}

    if selected_action == "Click":
        col1, col2 = st.columns(2)
        with col1:
            config["x"] = st.number_input("X Coordinate", value=0)
        with col2:
            config["y"] = st.number_input("Y Coordinate", value=0)

    elif selected_action == "Type Text":
        config["text"] = st.text_input("Text to Type")

    elif selected_action == "Wait":
        config["duration"] = st.number_input("Duration (seconds)", value=1.0)

    elif selected_action == "Condition":
        col1, col2, col3 = st.columns(3)
        with col1:
            config["left"] = st.text_input("Left Value")
        with col2:
            config["operator"] = st.selectbox(
                "Operator", ["==", "!=", ">", "<", ">=", "<=", "in", "contains"]
            )
        with col3:
            config["right"] = st.text_input("Right Value")

    elif selected_action == "Set Variable":
        col1, col2 = st.columns(2)
        with col1:
            config["name"] = st.text_input("Variable Name")
        with col2:
            config["value"] = st.text_input("Variable Value")

    elif selected_action == "HTTP Request":
        config["url"] = st.text_input("URL")
        col1, col2 = st.columns(2)
        with col1:
            config["method"] = st.selectbox("Method", ["GET", "POST", "PUT", "DELETE"])
        with col2:
            config["store_as"] = st.text_input("Store Response As (variable name)")

    elif selected_action == "Log Message":
        config["message"] = st.text_input("Message")
        config["level"] = st.selectbox("Level", ["INFO", "WARNING", "ERROR"])

    if st.button("Add Action to Workflow"):
        import uuid

        node_id = str(uuid.uuid4())
        new_node = {
            "id": node_id,
            "type": action_types[selected_action],
            "name": node_name,
            "config": config,
            "position": {"x": 100, "y": len(automation["workflow"]["nodes"]) * 100},
        }

        automation["workflow"]["nodes"].append(new_node)

        # Add edge from previous node
        if len(automation["workflow"]["nodes"]) > 1:
            prev_node_id = automation["workflow"]["nodes"][-2]["id"]
            edge_id = str(uuid.uuid4())
            automation["workflow"]["edges"].append(
                {"id": edge_id, "source": prev_node_id, "target": node_id}
            )

        st.success(f"Added {selected_action} action to workflow")

    # Display current workflow
    st.markdown("#### Current Workflow")

    if automation["workflow"]["nodes"]:
        for i, node in enumerate(automation["workflow"]["nodes"]):
            with st.expander(f"{i + 1}. {node['name']} ({node['type']})"):
                st.json(node["config"])

                if st.button("Remove", key=f"remove_{node['id']}"):
                    automation["workflow"]["nodes"].remove(node)
                    # Remove associated edges
                    automation["workflow"]["edges"] = [
                        e
                        for e in automation["workflow"]["edges"]
                        if e["source"] != node["id"] and e["target"] != node["id"]
                    ]
                    st.rerun()
    else:
        st.info("No actions in workflow yet")

    # Save workflow
    if st.button("💾 Save Workflow", type="primary"):
        try:
            response = requests.put(
                f"{API_URL}/api/v1/rpa/automations/{automation['id']}",
                json={"workflow": automation["workflow"]},
            )

            if response.status_code == 200:
                st.success("Workflow saved successfully!")
            else:
                st.error(f"Failed to save: {response.json()}")
        except Exception as e:
            st.error(f"Error saving workflow: {str(e)}")


def show_test_deploy():
    """Show test and deploy section"""
    st.markdown("### Test & Deploy")

    if "current_automation" not in st.session_state:
        st.info("Please create or select an automation first")
        return

    automation = st.session_state.current_automation

    # Test section
    st.markdown("#### Test Automation")

    input_data = st.text_area(
        "Input Data (JSON)",
        value="{}",
        help="Provide input data for testing",
    )

    if st.button("🧪 Test Run"):
        try:
            input_dict = json.loads(input_data)

            execution_data = {
                "automation_id": automation["id"],
                "trigger_type": "manual",
                "input_data": input_dict,
                "triggered_by": st.session_state.current_user,
            }

            response = requests.post(
                f"{API_URL}/api/v1/rpa/automations/{automation['id']}/execute",
                json=execution_data,
            )

            if response.status_code == 200:
                execution = response.json()
                st.success(f"Test execution started! Execution ID: {execution['id']}")
                st.json(execution)
            else:
                st.error(f"Failed to start execution: {response.json()}")
        except json.JSONDecodeError:
            st.error("Invalid JSON in input data")
        except Exception as e:
            st.error(f"Error: {str(e)}")

    # Deploy section
    st.markdown("---")
    st.markdown("#### Deploy Automation")

    current_status = automation.get("status", "draft")
    st.info(f"Current Status: **{current_status.upper()}**")

    if current_status == "draft":
        if st.button("✅ Activate Automation"):
            try:
                response = requests.put(
                    f"{API_URL}/api/v1/rpa/automations/{automation['id']}",
                    json={"status": "active"},
                )

                if response.status_code == 200:
                    st.success("Automation activated successfully!")
                    automation["status"] = "active"
                else:
                    st.error(f"Failed to activate: {response.json()}")
            except Exception as e:
                st.error(f"Error: {str(e)}")

    elif current_status == "active":
        col1, col2 = st.columns(2)

        with col1:
            if st.button("⏸️ Pause Automation"):
                try:
                    response = requests.put(
                        f"{API_URL}/api/v1/rpa/automations/{automation['id']}",
                        json={"status": "paused"},
                    )

                    if response.status_code == 200:
                        st.success("Automation paused")
                        automation["status"] = "paused"
                except Exception as e:
                    st.error(f"Error: {str(e)}")

        with col2:
            if st.button("📦 Archive Automation"):
                try:
                    response = requests.put(
                        f"{API_URL}/api/v1/rpa/automations/{automation['id']}",
                        json={"status": "archived"},
                    )

                    if response.status_code == 200:
                        st.success("Automation archived")
                        automation["status"] = "archived"
                except Exception as e:
                    st.error(f"Error: {str(e)}")
