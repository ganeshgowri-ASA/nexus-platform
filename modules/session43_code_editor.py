"""
Session 43: Code Editor
Features: Syntax highlighting, Git integration, terminal, AI code assistance
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


class CodeEditor:
    """Advanced Code Editor with Git and AI"""

    def __init__(self):
        """Initialize code editor"""
        if 'projects' not in st.session_state:
            st.session_state.projects = self.load_projects()
        if 'current_project' not in st.session_state:
            st.session_state.current_project = None
        if 'terminal_output' not in st.session_state:
            st.session_state.terminal_output = []

    def load_projects(self) -> List[Dict]:
        """Load saved projects"""
        projects = []
        files = storage.list_files('code_projects', '.json')
        for file in files:
            data = storage.load_json(file, 'code_projects')
            if data:
                projects.append(data)
        return projects

    def save_project(self, project: Dict) -> bool:
        """Save project"""
        filename = f"project_{project['id']}.json"
        return storage.save_json(filename, project, 'code_projects')

    def create_project(self, name: str, language: str) -> Dict:
        """Create new project"""
        return {
            'id': datetime.now().strftime('%Y%m%d_%H%M%S'),
            'name': name,
            'language': language,
            'created': datetime.now().isoformat(),
            'modified': datetime.now().isoformat(),
            'files': [],
            'git_enabled': False,
            'git_commits': []
        }

    def render(self):
        """Render code editor"""
        st.title("💻 Code Editor")
        st.markdown("*Professional code editor with syntax highlighting, Git, and terminal*")

        # Sidebar
        with st.sidebar:
            st.header("Projects")

            with st.expander("➕ New Project", expanded=False):
                new_name = st.text_input("Project Name", key="new_project_name")
                language = st.selectbox(
                    "Language",
                    ["Python", "JavaScript", "TypeScript", "Java", "C++", "Go", "Rust", "HTML/CSS", "SQL"]
                )
                if st.button("Create Project", type="primary"):
                    if new_name:
                        project = self.create_project(new_name, language)
                        st.session_state.projects.append(project)
                        st.session_state.current_project = project
                        self.save_project(project)
                        st.success(f"Created '{new_name}'")
                        st.rerun()

            if st.session_state.projects:
                for project in st.session_state.projects:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        if st.button(f"{project['name']} ({project['language']})", key=f"load_{project['id']}"):
                            st.session_state.current_project = project
                            st.rerun()
                    with col2:
                        if st.button("🗑️", key=f"del_{project['id']}"):
                            storage.delete_file(f"project_{project['id']}.json", 'code_projects')
                            st.session_state.projects.remove(project)
                            st.rerun()

        if st.session_state.current_project:
            project = st.session_state.current_project

            tabs = st.tabs(["📝 Editor", "📁 Files", "🔀 Git", "⚡ Terminal", "🤖 AI Assistant"])

            with tabs[0]:
                st.subheader(f"Project: {project['name']}")

                # File selector
                if project['files']:
                    selected_file_idx = st.selectbox(
                        "Open File",
                        range(len(project['files'])),
                        format_func=lambda x: project['files'][x]['name']
                    )

                    current_file = project['files'][selected_file_idx]

                    # Language mapping for syntax highlighting
                    lang_map = {
                        'Python': 'python',
                        'JavaScript': 'javascript',
                        'TypeScript': 'typescript',
                        'Java': 'java',
                        'C++': 'cpp',
                        'Go': 'go',
                        'Rust': 'rust',
                        'HTML/CSS': 'html',
                        'SQL': 'sql'
                    }

                    # Try to use ace editor for better editing
                    try:
                        from streamlit_ace import st_ace
                        code_content = st_ace(
                            value=current_file['content'],
                            language=lang_map.get(current_file['language'], 'python'),
                            theme='monokai',
                            height=500,
                            key=f"ace_{selected_file_idx}"
                        )
                        current_file['content'] = code_content
                    except ImportError:
                        # Fallback to text area
                        code_content = st.text_area(
                            "Code",
                            value=current_file['content'],
                            height=500,
                            key=f"code_{selected_file_idx}"
                        )
                        current_file['content'] = code_content

                    # Editor toolbar
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        if st.button("💾 Save"):
                            project['modified'] = datetime.now().isoformat()
                            self.save_project(project)
                            st.success("File saved!")

                    with col2:
                        if st.button("▶️ Run"):
                            st.info("Code execution coming soon!")

                    with col3:
                        # Line count
                        lines = len(code_content.split('\n'))
                        st.metric("Lines", lines)

                    with col4:
                        # Character count
                        st.metric("Characters", len(code_content))

                    # Code stats
                    with st.expander("📊 Code Statistics"):
                        words = len(code_content.split())
                        st.write(f"Words: {words}")
                        st.write(f"Lines: {lines}")
                        st.write(f"Characters: {len(code_content)}")

                else:
                    st.info("No files in this project. Create one in the Files tab!")

            with tabs[1]:
                st.subheader("📁 File Manager")

                with st.expander("➕ New File", expanded=True):
                    file_name = st.text_input("File Name (with extension)")
                    file_language = st.selectbox(
                        "Language",
                        ["Python", "JavaScript", "TypeScript", "Java", "C++", "Go", "Rust", "HTML/CSS", "SQL"],
                        index=0
                    )

                    if st.button("Create File"):
                        if file_name:
                            project['files'].append({
                                'name': file_name,
                                'language': file_language,
                                'content': f"# {file_name}\n# Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n",
                                'created': datetime.now().isoformat()
                            })
                            self.save_project(project)
                            st.success(f"Created '{file_name}'")
                            st.rerun()

                # File list
                if project['files']:
                    st.markdown("### Project Files")
                    for idx, file in enumerate(project['files']):
                        col1, col2, col3 = st.columns([3, 1, 1])
                        with col1:
                            st.write(f"📄 {file['name']}")
                        with col2:
                            st.write(file['language'])
                        with col3:
                            if st.button("🗑️", key=f"del_file_{idx}"):
                                project['files'].pop(idx)
                                self.save_project(project)
                                st.rerun()

            with tabs[2]:
                st.subheader("🔀 Git Integration")

                # Enable Git
                git_enabled = st.checkbox("Enable Git", value=project.get('git_enabled', False))
                project['git_enabled'] = git_enabled

                if git_enabled:
                    # Commit
                    with st.expander("📝 Create Commit"):
                        commit_message = st.text_input("Commit Message")
                        if st.button("Commit Changes"):
                            if commit_message:
                                project['git_commits'].append({
                                    'message': commit_message,
                                    'timestamp': datetime.now().isoformat(),
                                    'files_count': len(project['files'])
                                })
                                self.save_project(project)
                                st.success("Changes committed!")
                                st.rerun()

                    # Commit history
                    if project.get('git_commits'):
                        st.markdown("### 📜 Commit History")
                        for commit in reversed(project['git_commits']):
                            st.markdown(f"**{commit['message']}**")
                            st.caption(f"{commit['timestamp']} - {commit['files_count']} files")
                            st.markdown("---")
                    else:
                        st.info("No commits yet!")

                    # Git commands
                    st.markdown("### ⚡ Quick Git Commands")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("📥 Pull"):
                            st.info("Pull from remote")
                    with col2:
                        if st.button("📤 Push"):
                            st.info("Push to remote")
                    with col3:
                        if st.button("🌿 Branch"):
                            st.info("Create branch")

                else:
                    st.info("Enable Git to use version control features")

            with tabs[3]:
                st.subheader("⚡ Integrated Terminal")

                command = st.text_input("Command", placeholder="Enter command to execute")

                if st.button("Run Command", type="primary") or (command and st.session_state.get('auto_run')):
                    if command:
                        # Simulate terminal output
                        output = f"$ {command}\n"
                        if command.startswith('ls'):
                            output += "\n".join([f['name'] for f in project['files']])
                        elif command.startswith('pwd'):
                            output += f"/projects/{project['name']}"
                        elif command.startswith('echo'):
                            output += command[5:]
                        else:
                            output += f"Command '{command}' executed\n(Terminal simulation)"

                        st.session_state.terminal_output.append({
                            'command': command,
                            'output': output,
                            'timestamp': datetime.now().strftime('%H:%M:%S')
                        })

                # Terminal output
                st.markdown("### Terminal Output")
                terminal_display = st.container()
                with terminal_display:
                    for entry in st.session_state.terminal_output[-10:]:  # Last 10 commands
                        st.code(f"[{entry['timestamp']}] {entry['output']}", language='bash')

                if st.button("🗑️ Clear Terminal"):
                    st.session_state.terminal_output = []
                    st.rerun()

            with tabs[4]:
                st.subheader("🤖 AI Code Assistant")

                ai_action = st.radio(
                    "AI Action",
                    ["Explain Code", "Find Bugs", "Suggest Improvements", "Generate Code", "Write Tests"]
                )

                if ai_action == "Explain Code":
                    if project['files']:
                        file_idx = st.selectbox("Select File", range(len(project['files'])), format_func=lambda x: project['files'][x]['name'], key="explain_file")
                        if st.button("Explain"):
                            with st.spinner("Analyzing code..."):
                                code = project['files'][file_idx]['content']
                                language = project['files'][file_idx]['language']
                                explanation = ai_assistant.analyze_code(code, language)
                                st.markdown(explanation)

                elif ai_action == "Find Bugs":
                    if project['files']:
                        file_idx = st.selectbox("Select File", range(len(project['files'])), format_func=lambda x: project['files'][x]['name'], key="bug_file")
                        if st.button("Find Bugs"):
                            with st.spinner("Searching for bugs..."):
                                code = project['files'][file_idx]['content']
                                language = project['files'][file_idx]['language']
                                prompt = f"Find potential bugs and issues in this {language} code:\n\n```{language}\n{code}\n```"
                                bugs = ai_assistant.generate(prompt, max_tokens=1000)
                                st.markdown(bugs)

                elif ai_action == "Suggest Improvements":
                    if project['files']:
                        file_idx = st.selectbox("Select File", range(len(project['files'])), format_func=lambda x: project['files'][x]['name'], key="improve_file")
                        if st.button("Get Suggestions"):
                            with st.spinner("Analyzing..."):
                                code = project['files'][file_idx]['content']
                                language = project['files'][file_idx]['language']
                                suggestions = ai_assistant.suggest_code_improvements(code, language)
                                st.markdown(suggestions)

                elif ai_action == "Generate Code":
                    description = st.text_area("Describe what you want to build")
                    target_language = st.selectbox("Target Language", ["Python", "JavaScript", "TypeScript", "Java"])

                    if st.button("Generate"):
                        if description:
                            with st.spinner("Generating code..."):
                                prompt = f"Write {target_language} code for: {description}"
                                code = ai_assistant.generate(prompt, max_tokens=2000)
                                st.code(code, language=target_language.lower())

                                if st.button("💾 Save as New File"):
                                    project['files'].append({
                                        'name': f"ai_generated_{len(project['files'])+1}.{target_language.lower()[:2]}",
                                        'language': target_language,
                                        'content': code,
                                        'created': datetime.now().isoformat()
                                    })
                                    self.save_project(project)
                                    st.success("File saved!")
                                    st.rerun()

                else:  # Write Tests
                    if project['files']:
                        file_idx = st.selectbox("Select File to Test", range(len(project['files'])), format_func=lambda x: project['files'][x]['name'], key="test_file")
                        if st.button("Generate Tests"):
                            with st.spinner("Writing tests..."):
                                code = project['files'][file_idx]['content']
                                language = project['files'][file_idx]['language']
                                prompt = f"Write comprehensive unit tests for this {language} code:\n\n```{language}\n{code}\n```"
                                tests = ai_assistant.generate(prompt, max_tokens=2000)
                                st.code(tests, language=language.lower())

        else:
            st.info("👈 Create or select a project to get started")


def main():
    """Main entry point"""
    editor = CodeEditor()
    editor.render()


if __name__ == "__main__":
    main()
