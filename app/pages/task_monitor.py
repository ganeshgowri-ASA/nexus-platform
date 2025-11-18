"""
Task Monitoring Dashboard
Real-time monitoring of Celery background tasks
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json

from config.celery_config import celery_app
from config.settings import settings
from app.utils.task_stats import get_task_statistics, get_worker_stats, get_queue_lengths


def show_task_monitor():
    """Display task monitoring dashboard"""

    st.title("🔍 Task Monitoring Dashboard")
    st.markdown("Real-time monitoring of Celery background tasks")

    # Auto-refresh toggle
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("---")
    with col2:
        auto_refresh = st.checkbox("Auto-refresh", value=False)

    if auto_refresh:
        st.rerun()

    # Refresh button
    if st.button("🔄 Refresh Data", type="primary"):
        st.rerun()

    # Get current statistics
    try:
        task_stats = get_task_statistics()
        worker_stats = get_worker_stats()
        queue_lengths = get_queue_lengths()

        # Overview metrics
        st.subheader("📊 Overview")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                label="Active Tasks",
                value=task_stats.get('active_tasks', 0)
            )

        with col2:
            st.metric(
                label="Active Workers",
                value=task_stats.get('active_workers', 0)
            )

        with col3:
            st.metric(
                label="Scheduled Tasks",
                value=task_stats.get('scheduled_tasks', 0)
            )

        with col4:
            st.metric(
                label="Registered Tasks",
                value=task_stats.get('registered_tasks', 0)
            )

        # Queue Status
        st.subheader("📬 Queue Status")

        if queue_lengths:
            # Create queue status dataframe
            queue_df = pd.DataFrame([
                {'Queue': name, 'Tasks': length}
                for name, length in queue_lengths.items()
            ])

            col1, col2 = st.columns([2, 1])

            with col1:
                # Bar chart of queue lengths
                fig = px.bar(
                    queue_df,
                    x='Queue',
                    y='Tasks',
                    title='Tasks in Queues',
                    color='Tasks',
                    color_continuous_scale='Blues'
                )
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                # Queue table
                st.dataframe(
                    queue_df,
                    use_container_width=True,
                    hide_index=True
                )
        else:
            st.info("No queue data available")

        # Worker Information
        st.subheader("👷 Worker Information")

        if worker_stats.get('status') == 'ok':
            workers = worker_stats.get('workers', {})

            for worker_name, worker_info in workers.items():
                with st.expander(f"Worker: {worker_name}"):
                    st.json(worker_info)
        else:
            st.warning(f"Worker Status: {worker_stats.get('message', 'Unknown')}")

        # Active Tasks
        st.subheader("⚡ Active Tasks")

        if task_stats.get('workers'):
            active_tasks = []
            for worker, tasks in task_stats['workers'].items():
                for task in tasks:
                    active_tasks.append({
                        'Worker': worker,
                        'Task Name': task.get('name', 'Unknown'),
                        'Task ID': task.get('id', 'Unknown')[:8] + '...',
                        'Started': datetime.fromtimestamp(task.get('time_start', 0)).strftime('%H:%M:%S') if task.get('time_start') else 'N/A'
                    })

            if active_tasks:
                st.dataframe(
                    pd.DataFrame(active_tasks),
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("No active tasks")
        else:
            st.info("No active tasks")

        # Registered Tasks
        st.subheader("📋 Registered Tasks")

        if 'task_list' in task_stats:
            task_list = task_stats['task_list']

            # Group tasks by module
            task_groups = {}
            for task in task_list:
                module = task.split('.')[0] if '.' in task else 'Other'
                if module not in task_groups:
                    task_groups[module] = []
                task_groups[module].append(task)

            for module, tasks in task_groups.items():
                with st.expander(f"📦 {module} ({len(tasks)} tasks)"):
                    for task in sorted(tasks):
                        st.text(f"• {task}")
        else:
            st.info("No registered tasks found")

        # Task Execution Section
        st.markdown("---")
        st.subheader("🚀 Execute Test Tasks")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Test Email Task"):
                try:
                    from app.tasks.email_tasks import send_notification
                    task = send_notification.delay(
                        user_email="test@example.com",
                        notification_type="task_complete",
                        context={'task_name': 'Test Task', 'details': 'This is a test'}
                    )
                    st.success(f"Email task queued: {task.id}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

        with col2:
            if st.button("Test Health Check"):
                try:
                    from app.tasks.maintenance_tasks import health_check
                    task = health_check.delay()
                    st.success(f"Health check queued: {task.id}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

        # Task Result Checker
        st.markdown("---")
        st.subheader("🔎 Check Task Result")

        task_id = st.text_input("Enter Task ID:")
        if st.button("Get Result") and task_id:
            try:
                from celery.result import AsyncResult
                result = AsyncResult(task_id, app=celery_app)

                st.write(f"**Status:** {result.status}")
                st.write(f"**State:** {result.state}")

                if result.ready():
                    st.write("**Result:**")
                    st.json(result.result)
                else:
                    st.info("Task is still processing...")

            except Exception as e:
                st.error(f"Error: {str(e)}")

    except Exception as e:
        st.error(f"Error loading dashboard: {str(e)}")
        st.exception(e)

    # Footer
    st.markdown("---")
    st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    show_task_monitor()
