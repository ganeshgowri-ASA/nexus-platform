"""
Session 45: Blog Platform
Features: Posts, categories, comments, themes, AI content generation
"""
import streamlit as st
import json
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from utils.ai_assistant import ai_assistant
from utils.storage import storage


class BlogPlatform:
    """Full-featured blog platform with AI assistance"""

    def __init__(self):
        """Initialize blog platform"""
        if 'blogs' not in st.session_state:
            st.session_state.blogs = self.load_blogs()
        if 'current_blog' not in st.session_state:
            st.session_state.current_blog = None

    def load_blogs(self) -> List[Dict]:
        """Load saved blogs"""
        blogs = []
        files = storage.list_files('blogs', '.json')
        for file in files:
            data = storage.load_json(file, 'blogs')
            if data:
                blogs.append(data)
        return blogs

    def save_blog(self, blog: Dict) -> bool:
        """Save blog"""
        filename = f"blog_{blog['id']}.json"
        return storage.save_json(filename, blog, 'blogs')

    def create_blog(self, name: str, description: str) -> Dict:
        """Create new blog"""
        return {
            'id': datetime.now().strftime('%Y%m%d_%H%M%S'),
            'name': name,
            'description': description,
            'created': datetime.now().isoformat(),
            'modified': datetime.now().isoformat(),
            'posts': [],
            'categories': ['Uncategorized'],
            'tags': [],
            'comments': [],
            'theme': {
                'name': 'Modern',
                'primaryColor': '#2c3e50',
                'accentColor': '#3498db'
            },
            'settings': {
                'allow_comments': True,
                'posts_per_page': 10
            }
        }

    def themes(self) -> List[str]:
        """Available themes"""
        return ['Modern', 'Classic', 'Minimal', 'Magazine', 'Tech', 'Creative']

    def render(self):
        """Render blog platform"""
        st.title("✍️ Blog Platform")
        st.markdown("*Create and manage your blog with AI-powered content generation*")

        # Sidebar
        with st.sidebar:
            st.header("Blogs")

            with st.expander("➕ New Blog", expanded=False):
                new_name = st.text_input("Blog Name", key="new_blog_name")
                new_desc = st.text_area("Description", key="new_blog_desc")
                if st.button("Create Blog", type="primary"):
                    if new_name:
                        blog = self.create_blog(new_name, new_desc)
                        st.session_state.blogs.append(blog)
                        st.session_state.current_blog = blog
                        self.save_blog(blog)
                        st.success(f"Created '{new_name}'")
                        st.rerun()

            if st.session_state.blogs:
                for blog in st.session_state.blogs:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        if st.button(blog['name'], key=f"load_{blog['id']}"):
                            st.session_state.current_blog = blog
                            st.rerun()
                    with col2:
                        if st.button("🗑️", key=f"del_{blog['id']}"):
                            storage.delete_file(f"blog_{blog['id']}.json", 'blogs')
                            st.session_state.blogs.remove(blog)
                            st.rerun()

        if st.session_state.current_blog:
            blog = st.session_state.current_blog

            tabs = st.tabs(["📝 Posts", "📁 Categories", "💬 Comments", "🎨 Theme", "🤖 AI Writer", "👁️ Preview", "📊 Analytics"])

            with tabs[0]:
                st.subheader(f"Blog: {blog['name']}")
                st.caption(blog['description'])

                # New post
                with st.expander("➕ New Post", expanded=True):
                    post_title = st.text_input("Post Title")
                    post_category = st.selectbox("Category", blog['categories'])
                    post_tags = st.text_input("Tags (comma-separated)")
                    post_content = st.text_area("Content", height=300)

                    col1, col2 = st.columns(2)
                    with col1:
                        post_status = st.selectbox("Status", ["Draft", "Published", "Scheduled"])
                    with col2:
                        featured = st.checkbox("Featured Post")

                    if st.button("Create Post", type="primary"):
                        if post_title and post_content:
                            blog['posts'].append({
                                'id': f"post_{len(blog['posts'])+1}",
                                'title': post_title,
                                'content': post_content,
                                'category': post_category,
                                'tags': [t.strip() for t in post_tags.split(',') if t.strip()],
                                'status': post_status,
                                'featured': featured,
                                'author': 'Admin',
                                'created': datetime.now().isoformat(),
                                'modified': datetime.now().isoformat(),
                                'views': 0,
                                'likes': 0
                            })

                            # Add new tags to blog tags
                            for tag in [t.strip() for t in post_tags.split(',') if t.strip()]:
                                if tag not in blog['tags']:
                                    blog['tags'].append(tag)

                            blog['modified'] = datetime.now().isoformat()
                            self.save_blog(blog)
                            st.success(f"Post '{post_title}' created!")
                            st.rerun()

                # Display posts
                if blog['posts']:
                    st.markdown("### Published Posts")

                    # Filter options
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        filter_category = st.selectbox("Filter by Category", ["All"] + blog['categories'], key="filter_cat")
                    with col2:
                        filter_status = st.selectbox("Filter by Status", ["All", "Draft", "Published", "Scheduled"], key="filter_status")
                    with col3:
                        sort_by = st.selectbox("Sort by", ["Newest", "Oldest", "Most Viewed", "Most Liked"])

                    # Apply filters
                    filtered_posts = blog['posts']
                    if filter_category != "All":
                        filtered_posts = [p for p in filtered_posts if p['category'] == filter_category]
                    if filter_status != "All":
                        filtered_posts = [p for p in filtered_posts if p['status'] == filter_status]

                    # Sort
                    if sort_by == "Newest":
                        filtered_posts = sorted(filtered_posts, key=lambda x: x['created'], reverse=True)
                    elif sort_by == "Oldest":
                        filtered_posts = sorted(filtered_posts, key=lambda x: x['created'])
                    elif sort_by == "Most Viewed":
                        filtered_posts = sorted(filtered_posts, key=lambda x: x.get('views', 0), reverse=True)
                    elif sort_by == "Most Liked":
                        filtered_posts = sorted(filtered_posts, key=lambda x: x.get('likes', 0), reverse=True)

                    # Display filtered posts
                    for idx, post in enumerate(filtered_posts):
                        with st.expander(f"{'⭐ ' if post.get('featured') else ''}{post['title']} - {post['status']}"):
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.write(f"**Category:** {post['category']}")
                            with col2:
                                st.write(f"**Tags:** {', '.join(post.get('tags', []))}")
                            with col3:
                                st.write(f"**Views:** {post.get('views', 0)} | **Likes:** {post.get('likes', 0)}")

                            st.markdown(f"**Content Preview:**")
                            st.write(post['content'][:200] + "..." if len(post['content']) > 200 else post['content'])

                            col_a, col_b, col_c = st.columns(3)
                            with col_a:
                                if st.button("✏️ Edit", key=f"edit_post_{post['id']}"):
                                    st.info("Edit mode - Update post content above")
                            with col_b:
                                if st.button("📊 Stats", key=f"stats_post_{post['id']}"):
                                    st.metric("Views", post.get('views', 0))
                                    st.metric("Likes", post.get('likes', 0))
                            with col_c:
                                if st.button("🗑️ Delete", key=f"del_post_{post['id']}"):
                                    blog['posts'] = [p for p in blog['posts'] if p['id'] != post['id']]
                                    self.save_blog(blog)
                                    st.rerun()

                    st.info(f"Showing {len(filtered_posts)} of {len(blog['posts'])} posts")

                else:
                    st.info("No posts yet. Create your first post!")

            with tabs[1]:
                st.subheader("📁 Categories")

                # Add category
                with st.expander("➕ Add Category"):
                    new_category = st.text_input("Category Name")
                    if st.button("Add Category"):
                        if new_category and new_category not in blog['categories']:
                            blog['categories'].append(new_category)
                            self.save_blog(blog)
                            st.success(f"Category '{new_category}' added!")
                            st.rerun()

                # Display categories
                st.markdown("### Current Categories")
                for idx, category in enumerate(blog['categories']):
                    post_count = len([p for p in blog['posts'] if p['category'] == category])

                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        st.write(f"📁 {category}")
                    with col2:
                        st.write(f"{post_count} posts")
                    with col3:
                        if category != "Uncategorized":
                            if st.button("🗑️", key=f"del_cat_{idx}"):
                                blog['categories'].remove(category)
                                self.save_blog(blog)
                                st.rerun()

                # Tags
                st.markdown("### 🏷️ Tags")
                if blog['tags']:
                    st.write(", ".join(blog['tags']))
                else:
                    st.info("No tags yet. Tags are automatically added when you create posts.")

            with tabs[2]:
                st.subheader("💬 Comments")

                if blog['settings']['allow_comments']:
                    # Comment moderation
                    st.markdown("### Recent Comments")

                    # Simulate comments for display
                    if not blog.get('comments'):
                        blog['comments'] = []

                    # Add test comment
                    with st.expander("➕ Moderate Comments"):
                        post_select = st.selectbox("Select Post", [p['title'] for p in blog['posts']]) if blog['posts'] else None

                        if post_select:
                            st.info(f"Comments for: {post_select}")

                    if blog['comments']:
                        for idx, comment in enumerate(blog['comments']):
                            with st.container():
                                col1, col2 = st.columns([4, 1])
                                with col1:
                                    st.markdown(f"**{comment.get('author', 'Anonymous')}** on {comment.get('post', 'Unknown Post')}")
                                    st.write(comment.get('content', ''))
                                with col2:
                                    if st.button("✅ Approve", key=f"approve_{idx}"):
                                        blog['comments'][idx]['approved'] = True
                                        self.save_blog(blog)
                                        st.rerun()
                                    if st.button("🗑️ Delete", key=f"del_comment_{idx}"):
                                        blog['comments'].pop(idx)
                                        self.save_blog(blog)
                                        st.rerun()
                                st.markdown("---")
                    else:
                        st.info("No comments yet!")

                else:
                    st.warning("Comments are disabled. Enable them in settings.")

                # Comment settings
                st.markdown("### ⚙️ Comment Settings")
                allow_comments = st.checkbox("Allow Comments", value=blog['settings']['allow_comments'])
                blog['settings']['allow_comments'] = allow_comments

                if st.button("💾 Save Settings"):
                    self.save_blog(blog)
                    st.success("Settings saved!")

            with tabs[3]:
                st.subheader("🎨 Theme Customization")

                theme_name = st.selectbox("Select Theme", self.themes(), index=self.themes().index(blog['theme']['name']))
                blog['theme']['name'] = theme_name

                col1, col2 = st.columns(2)
                with col1:
                    primary_color = st.color_picker("Primary Color", blog['theme']['primaryColor'])
                    blog['theme']['primaryColor'] = primary_color
                with col2:
                    accent_color = st.color_picker("Accent Color", blog['theme']['accentColor'])
                    blog['theme']['accentColor'] = accent_color

                # Layout options
                st.markdown("### Layout Options")
                layout = st.radio("Layout Style", ["Single Column", "Two Column", "Grid"])

                # Display options
                st.markdown("### Display Options")
                col1, col2 = st.columns(2)
                with col1:
                    show_sidebar = st.checkbox("Show Sidebar", value=True)
                    show_author = st.checkbox("Show Author", value=True)
                with col2:
                    show_dates = st.checkbox("Show Dates", value=True)
                    show_categories = st.checkbox("Show Categories", value=True)

                if st.button("💾 Save Theme"):
                    blog['modified'] = datetime.now().isoformat()
                    self.save_blog(blog)
                    st.success("Theme saved!")

                # Preview theme
                st.markdown("### Theme Preview")
                preview_html = f"""
                <div style="padding: 20px; background: white; border-radius: 8px; border: 2px solid {primary_color};">
                    <h1 style="color: {primary_color};">{blog['name']}</h1>
                    <p style="color: #666;">{blog['description']}</p>
                    <div style="margin-top: 20px; padding: 15px; background: {accent_color}20; border-left: 4px solid {accent_color};">
                        <h3 style="color: {accent_color};">Sample Blog Post</h3>
                        <p>This is how your blog posts will look with the selected theme.</p>
                    </div>
                </div>
                """
                st.components.v1.html(preview_html, height=250)

            with tabs[4]:
                st.subheader("🤖 AI Content Writer")

                ai_mode = st.radio("AI Mode", ["Generate Post", "Improve Existing", "Generate Ideas", "SEO Optimization"])

                if ai_mode == "Generate Post":
                    topic = st.text_input("Post Topic")
                    keywords = st.text_input("Target Keywords (comma-separated)")
                    tone = st.selectbox("Tone", ["Professional", "Casual", "Technical", "Creative", "Informative"])
                    length = st.slider("Approximate Word Count", 300, 2000, 800)

                    if st.button("✨ Generate Post"):
                        if topic:
                            with st.spinner("Writing post..."):
                                keyword_list = [k.strip() for k in keywords.split(',') if k.strip()]
                                post_content = ai_assistant.generate_blog_post(topic, keyword_list, tone)

                                st.markdown("### Generated Post")
                                st.markdown(post_content)

                                if st.button("💾 Save as Draft"):
                                    blog['posts'].append({
                                        'id': f"post_{len(blog['posts'])+1}",
                                        'title': topic,
                                        'content': post_content,
                                        'category': 'Uncategorized',
                                        'tags': keyword_list,
                                        'status': 'Draft',
                                        'featured': False,
                                        'author': 'AI Assistant',
                                        'created': datetime.now().isoformat(),
                                        'modified': datetime.now().isoformat(),
                                        'views': 0,
                                        'likes': 0
                                    })
                                    self.save_blog(blog)
                                    st.success("Post saved as draft!")
                                    st.rerun()

                elif ai_mode == "Improve Existing":
                    if blog['posts']:
                        post_to_improve = st.selectbox("Select Post", blog['posts'], format_func=lambda x: x['title'])

                        if st.button("✨ Improve Post"):
                            with st.spinner("Improving post..."):
                                prompt = f"Improve this blog post:\n\nTitle: {post_to_improve['title']}\n\nContent:\n{post_to_improve['content']}"
                                improved = ai_assistant.generate(prompt, max_tokens=2000)
                                st.markdown("### Improved Version")
                                st.markdown(improved)

                                if st.button("💾 Update Post"):
                                    post_to_improve['content'] = improved
                                    post_to_improve['modified'] = datetime.now().isoformat()
                                    self.save_blog(blog)
                                    st.success("Post updated!")
                                    st.rerun()
                    else:
                        st.info("No posts to improve. Create a post first!")

                elif ai_mode == "Generate Ideas":
                    niche = st.text_input("Blog Niche/Topic")
                    num_ideas = st.slider("Number of Ideas", 5, 20, 10)

                    if st.button("💡 Generate Ideas"):
                        if niche:
                            with st.spinner("Generating ideas..."):
                                prompt = f"Generate {num_ideas} blog post ideas for a blog about {niche}"
                                ideas = ai_assistant.generate(prompt, max_tokens=1000)
                                st.markdown(ideas)

                else:  # SEO Optimization
                    if blog['posts']:
                        post_for_seo = st.selectbox("Select Post for SEO", blog['posts'], format_func=lambda x: x['title'])

                        if st.button("🔍 Analyze SEO"):
                            with st.spinner("Analyzing SEO..."):
                                prompt = f"Provide SEO recommendations for this blog post:\n\nTitle: {post_for_seo['title']}\n\nContent:\n{post_for_seo['content'][:500]}"
                                seo_tips = ai_assistant.generate(prompt, max_tokens=800)
                                st.markdown(seo_tips)
                    else:
                        st.info("Create posts first to analyze SEO!")

            with tabs[5]:
                st.subheader("👁️ Blog Preview")

                # Generate blog HTML preview
                preview_html = f"""
                <html>
                <head>
                    <style>
                        body {{
                            font-family: Arial, sans-serif;
                            max-width: 900px;
                            margin: 0 auto;
                            padding: 20px;
                            background: #f5f5f5;
                        }}
                        .header {{
                            background: {blog['theme']['primaryColor']};
                            color: white;
                            padding: 30px;
                            border-radius: 8px;
                            margin-bottom: 30px;
                        }}
                        .post {{
                            background: white;
                            padding: 25px;
                            margin-bottom: 20px;
                            border-radius: 8px;
                            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                        }}
                        .post h2 {{
                            color: {blog['theme']['primaryColor']};
                            margin-top: 0;
                        }}
                        .post-meta {{
                            color: #666;
                            font-size: 0.9em;
                            margin-bottom: 15px;
                        }}
                        .category {{
                            background: {blog['theme']['accentColor']};
                            color: white;
                            padding: 5px 10px;
                            border-radius: 4px;
                            font-size: 0.85em;
                        }}
                    </style>
                </head>
                <body>
                    <div class="header">
                        <h1>{blog['name']}</h1>
                        <p>{blog['description']}</p>
                    </div>
                """

                # Show recent posts
                recent_posts = sorted(blog['posts'], key=lambda x: x['created'], reverse=True)[:5]
                for post in recent_posts:
                    if post['status'] == 'Published' or True:  # Show all for preview
                        preview_html += f"""
                        <div class="post">
                            <h2>{post['title']}</h2>
                            <div class="post-meta">
                                <span class="category">{post['category']}</span> |
                                By {post['author']} |
                                {post['created'][:10]}
                            </div>
                            <p>{post['content'][:300]}...</p>
                        </div>
                        """

                preview_html += """
                </body>
                </html>
                """

                st.components.v1.html(preview_html, height=800, scrolling=True)

            with tabs[6]:
                st.subheader("📊 Blog Analytics")

                if blog['posts']:
                    # Stats
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total Posts", len(blog['posts']))
                    with col2:
                        published = len([p for p in blog['posts'] if p['status'] == 'Published'])
                        st.metric("Published", published)
                    with col3:
                        total_views = sum(p.get('views', 0) for p in blog['posts'])
                        st.metric("Total Views", total_views)
                    with col4:
                        total_likes = sum(p.get('likes', 0) for p in blog['posts'])
                        st.metric("Total Likes", total_likes)

                    # Posts by category
                    st.markdown("### Posts by Category")
                    category_counts = {}
                    for post in blog['posts']:
                        cat = post['category']
                        category_counts[cat] = category_counts.get(cat, 0) + 1

                    df = pd.DataFrame({
                        'Category': list(category_counts.keys()),
                        'Posts': list(category_counts.values())
                    })
                    st.bar_chart(df.set_index('Category'))

                    # Top posts
                    st.markdown("### Top Posts by Views")
                    top_posts = sorted(blog['posts'], key=lambda x: x.get('views', 0), reverse=True)[:5]
                    for post in top_posts:
                        st.write(f"- **{post['title']}** - {post.get('views', 0)} views")

                else:
                    st.info("No posts yet. Create posts to see analytics!")

                # Export analytics
                if st.button("📥 Export Analytics"):
                    analytics_data = {
                        'total_posts': len(blog['posts']),
                        'categories': blog['categories'],
                        'total_views': sum(p.get('views', 0) for p in blog['posts']),
                        'total_likes': sum(p.get('likes', 0) for p in blog['posts']),
                        'posts': blog['posts']
                    }
                    st.download_button(
                        "Download Analytics JSON",
                        json.dumps(analytics_data, indent=2),
                        file_name=f"{blog['name']}_analytics.json",
                        mime="application/json"
                    )

        else:
            st.info("👈 Create or select a blog to get started")

            st.markdown("""
            ## Welcome to Blog Platform! ✍️

            **Features:**
            - 📝 Rich post editor
            - 📁 Categories and tags
            - 💬 Comment system
            - 🎨 Customizable themes
            - 🤖 AI content generation
            - 📊 Analytics dashboard

            **Get Started:**
            1. Create a new blog
            2. Write your first post
            3. Customize your theme
            4. Use AI to generate content
            5. Track your analytics
            """)


def main():
    """Main entry point"""
    platform = BlogPlatform()
    platform.render()


if __name__ == "__main__":
    main()
