"""
Bots management page
"""
import streamlit as st
import requests

API_URL = "http://localhost:8000"


def show():
    """Display bots page"""
    st.markdown('<p class="main-header">🤖 Bots</p>', unsafe_allow_html=True)

    # Create new bot
    with st.expander("➕ Create New Bot"):
        with st.form("create_bot_form"):
            name = st.text_input("Bot Name*")
            description = st.text_area("Description")
            bot_type = st.selectbox(
                "Bot Type", ["standard", "ui_automation", "api", "data_processing"]
            )

            submitted = st.form_submit_button("Create Bot")

            if submitted and name:
                bot_data = {
                    "name": name,
                    "description": description,
                    "bot_type": bot_type,
                    "capabilities": [],
                    "configuration": {},
                    "created_by": st.session_state.current_user,
                }

                try:
                    response = requests.post(
                        f"{API_URL}/api/v1/rpa/bots", json=bot_data
                    )
                    if response.status_code == 200:
                        st.success(f"Bot '{name}' created successfully!")
                        st.rerun()
                    else:
                        st.error(f"Error: {response.json()}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

    # List bots
    st.markdown("### Existing Bots")

    try:
        response = requests.get(f"{API_URL}/api/v1/rpa/bots")

        if response.status_code == 200:
            bots = response.json()

            if bots:
                for bot in bots:
                    col1, col2, col3 = st.columns([3, 2, 2])

                    with col1:
                        st.markdown(f"### {bot['name']}")
                        st.caption(bot.get("description", "No description"))

                    with col2:
                        st.text(f"Type: {bot['bot_type']}")
                        st.text(f"Status: {bot['status']}")

                    with col3:
                        if st.button("🗑️ Delete", key=f"delete_{bot['id']}"):
                            try:
                                del_response = requests.delete(
                                    f"{API_URL}/api/v1/rpa/bots/{bot['id']}"
                                )
                                if del_response.status_code == 200:
                                    st.success("Bot deleted")
                                    st.rerun()
                            except Exception as e:
                                st.error(f"Error: {str(e)}")

                    st.markdown("---")
            else:
                st.info("No bots found")
        else:
            st.error("Failed to fetch bots")

    except Exception as e:
        st.error(f"Error: {str(e)}")
