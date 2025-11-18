"""
Session 42: API Tester
Features: Postman-like interface, collections, tests, AI-powered test generation
"""
import streamlit as st
import json
import requests
from datetime import datetime
from typing import Dict, List, Any
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from utils.ai_assistant import ai_assistant
from utils.storage import storage


class APITester:
    """API Testing tool like Postman"""

    def __init__(self):
        """Initialize API tester"""
        if 'collections' not in st.session_state:
            st.session_state.collections = self.load_collections()
        if 'current_collection' not in st.session_state:
            st.session_state.current_collection = None

    def load_collections(self) -> List[Dict]:
        """Load saved collections"""
        collections = []
        files = storage.list_files('api_tests', '.json')
        for file in files:
            data = storage.load_json(file, 'api_tests')
            if data:
                collections.append(data)
        return collections

    def save_collection(self, collection: Dict) -> bool:
        """Save collection"""
        filename = f"collection_{collection['id']}.json"
        return storage.save_json(filename, collection, 'api_tests')

    def create_collection(self, name: str) -> Dict:
        """Create new collection"""
        return {
            'id': datetime.now().strftime('%Y%m%d_%H%M%S'),
            'name': name,
            'created': datetime.now().isoformat(),
            'modified': datetime.now().isoformat(),
            'requests': [],
            'tests': [],
            'environment': {}
        }

    def execute_request(self, request: Dict) -> Dict:
        """Execute API request"""
        try:
            method = request.get('method', 'GET')
            url = request.get('url', '')
            headers = request.get('headers', {})
            body = request.get('body', '')

            # Parse headers
            if isinstance(headers, str):
                try:
                    headers = json.loads(headers)
                except:
                    headers = {}

            # Parse body
            data = None
            if body:
                try:
                    data = json.loads(body)
                except:
                    data = body

            # Execute request
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=data if isinstance(data, dict) else None,
                data=data if isinstance(data, str) else None,
                timeout=30
            )

            return {
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'body': response.text,
                'time': response.elapsed.total_seconds() * 1000,  # ms
                'success': True
            }

        except Exception as e:
            return {
                'error': str(e),
                'success': False
            }

    def render(self):
        """Render API tester"""
        st.title("🔌 API Tester")
        st.markdown("*Postman-like API testing with collections and AI assistance*")

        # Sidebar
        with st.sidebar:
            st.header("Collections")

            with st.expander("➕ New Collection", expanded=False):
                new_name = st.text_input("Collection Name", key="new_collection_name")
                if st.button("Create Collection", type="primary"):
                    if new_name:
                        collection = self.create_collection(new_name)
                        st.session_state.collections.append(collection)
                        st.session_state.current_collection = collection
                        self.save_collection(collection)
                        st.success(f"Created '{new_name}'")
                        st.rerun()

            if st.session_state.collections:
                for collection in st.session_state.collections:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        if st.button(collection['name'], key=f"load_{collection['id']}"):
                            st.session_state.current_collection = collection
                            st.rerun()
                    with col2:
                        if st.button("🗑️", key=f"del_{collection['id']}"):
                            storage.delete_file(f"collection_{collection['id']}.json", 'api_tests')
                            st.session_state.collections.remove(collection)
                            st.rerun()

        if st.session_state.current_collection:
            collection = st.session_state.current_collection

            tabs = st.tabs(["🚀 Request", "📚 Collection", "🧪 Tests", "🤖 AI Assistant", "🌐 Environment"])

            with tabs[0]:
                st.subheader("API Request")

                col1, col2 = st.columns([1, 3])
                with col1:
                    method = st.selectbox("Method", ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])
                with col2:
                    url = st.text_input("URL", placeholder="https://api.example.com/endpoint")

                # Headers
                st.markdown("**Headers**")
                headers_text = st.text_area(
                    "Headers (JSON format)",
                    value='{\n  "Content-Type": "application/json"\n}',
                    height=100
                )

                # Body (for POST, PUT, PATCH)
                if method in ["POST", "PUT", "PATCH"]:
                    st.markdown("**Body**")
                    body_type = st.radio("Body Type", ["JSON", "Raw", "Form Data"], horizontal=True)
                    body = st.text_area("Request Body", height=200)
                else:
                    body = ""

                # Execute request
                col1, col2 = st.columns([1, 4])
                with col1:
                    if st.button("▶️ Send Request", type="primary"):
                        if url:
                            with st.spinner("Sending request..."):
                                request_data = {
                                    'method': method,
                                    'url': url,
                                    'headers': headers_text,
                                    'body': body
                                }

                                result = self.execute_request(request_data)

                                # Store in session state for display
                                st.session_state['last_response'] = result

                                # Save to collection
                                if st.session_state.get('save_to_collection'):
                                    collection['requests'].append({
                                        'name': f"Request_{len(collection['requests'])+1}",
                                        'request': request_data,
                                        'created': datetime.now().isoformat()
                                    })
                                    self.save_collection(collection)

                                st.rerun()

                with col2:
                    st.checkbox("Save to collection", key='save_to_collection')

                # Display response
                if 'last_response' in st.session_state:
                    response = st.session_state['last_response']

                    st.markdown("---")
                    st.markdown("### Response")

                    if response.get('success'):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            status_code = response['status_code']
                            color = "🟢" if 200 <= status_code < 300 else "🔴"
                            st.metric("Status", f"{color} {status_code}")
                        with col2:
                            st.metric("Time", f"{response['time']:.0f} ms")
                        with col3:
                            st.metric("Size", f"{len(response['body'])} B")

                        # Response body
                        st.markdown("**Response Body:**")
                        try:
                            formatted_json = json.dumps(json.loads(response['body']), indent=2)
                            st.code(formatted_json, language='json')
                        except:
                            st.text_area("Response", response['body'], height=300)

                        # Response headers
                        with st.expander("Response Headers"):
                            st.json(response['headers'])

                    else:
                        st.error(f"Error: {response.get('error')}")

            with tabs[1]:
                st.subheader("📚 Request Collection")

                if collection['requests']:
                    for idx, req in enumerate(collection['requests']):
                        with st.expander(f"{req['name']} - {req['request']['method']} {req['request']['url']}"):
                            st.code(json.dumps(req['request'], indent=2), language='json')

                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button("🔄 Rerun", key=f"rerun_{idx}"):
                                    result = self.execute_request(req['request'])
                                    st.session_state['last_response'] = result
                                    st.rerun()
                            with col2:
                                if st.button("🗑️ Delete", key=f"del_req_{idx}"):
                                    collection['requests'].pop(idx)
                                    self.save_collection(collection)
                                    st.rerun()
                else:
                    st.info("No requests saved yet. Send a request and save it to the collection!")

                # Import/Export
                st.markdown("### 📤 Import/Export")
                col1, col2 = st.columns(2)
                with col1:
                    st.download_button(
                        "Export Collection",
                        json.dumps(collection, indent=2),
                        file_name=f"{collection['name']}.json",
                        mime="application/json"
                    )

            with tabs[2]:
                st.subheader("🧪 Test Scripts")

                st.markdown("Write assertions to validate API responses")

                test_name = st.text_input("Test Name")
                test_script = st.text_area(
                    "Test Script",
                    value="# Example:\n# assert response.status_code == 200\n# assert 'data' in response.json()",
                    height=200
                )

                if st.button("💾 Save Test"):
                    if test_name and test_script:
                        collection['tests'].append({
                            'name': test_name,
                            'script': test_script,
                            'created': datetime.now().isoformat()
                        })
                        self.save_collection(collection)
                        st.success("Test saved!")
                        st.rerun()

                # Display tests
                if collection['tests']:
                    st.markdown("### Saved Tests")
                    for idx, test in enumerate(collection['tests']):
                        with st.expander(test['name']):
                            st.code(test['script'], language='python')
                            if st.button("🗑️ Delete", key=f"del_test_{idx}"):
                                collection['tests'].pop(idx)
                                self.save_collection(collection)
                                st.rerun()

            with tabs[3]:
                st.subheader("🤖 AI Test Generator")

                endpoint_desc = st.text_input("Endpoint Description", placeholder="e.g., POST /users - Create new user")
                endpoint_method = st.selectbox("Method", ["GET", "POST", "PUT", "DELETE"], key="ai_method")
                endpoint_url = st.text_input("Endpoint URL", key="ai_url")

                if st.button("✨ Generate Tests"):
                    if endpoint_desc:
                        with st.spinner("Generating tests..."):
                            tests = ai_assistant.generate_api_test(endpoint_url, endpoint_method, endpoint_desc)
                            st.json(tests)

                            if st.button("💾 Add to Collection"):
                                collection['tests'].append({
                                    'name': f"AI_Test_{len(collection['tests'])+1}",
                                    'script': json.dumps(tests, indent=2),
                                    'created': datetime.now().isoformat()
                                })
                                self.save_collection(collection)
                                st.success("Tests added!")
                                st.rerun()

                # Generate request
                st.markdown("### Generate Request from Description")
                request_desc = st.text_area("Describe the API request you want to make")

                if st.button("Generate Request"):
                    if request_desc:
                        with st.spinner("Generating..."):
                            prompt = f"Generate an API request configuration (method, url, headers, body) for:\n{request_desc}"
                            suggestion = ai_assistant.generate(prompt, max_tokens=500)
                            st.markdown(suggestion)

            with tabs[4]:
                st.subheader("🌐 Environment Variables")

                st.markdown("Define variables to reuse across requests")

                with st.expander("➕ Add Variable"):
                    var_key = st.text_input("Key")
                    var_value = st.text_input("Value")

                    if st.button("Add Variable"):
                        if var_key:
                            collection['environment'][var_key] = var_value
                            self.save_collection(collection)
                            st.success("Variable added!")
                            st.rerun()

                # Display variables
                if collection['environment']:
                    st.markdown("### Variables")
                    for key, value in collection['environment'].items():
                        col1, col2, col3 = st.columns([2, 3, 1])
                        with col1:
                            st.write(f"**{key}**")
                        with col2:
                            st.code(value)
                        with col3:
                            if st.button("🗑️", key=f"del_env_{key}"):
                                del collection['environment'][key]
                                self.save_collection(collection)
                                st.rerun()
                else:
                    st.info("No environment variables yet!")

        else:
            st.info("👈 Create or select a collection to get started")


def main():
    """Main entry point"""
    tester = APITester()
    tester.render()


if __name__ == "__main__":
    main()
