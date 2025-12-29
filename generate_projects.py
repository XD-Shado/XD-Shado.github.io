import os

# Paths
projects_folder = "projects"
output_file = "index.html"

# HTML template parts
html_start = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>My Portfolio</title>
<link rel="stylesheet" href="style.css">
</head>
<body>
<header>
<h1>My Projects Portfolio</h1>
<p>Welcome! Here are some of my coding projects.</p>
</header>
<main>
<section class="projects">
"""

html_end = """
</section>
</main>
<footer>
<p>© 2025 Aaron Viegas</p>
</footer>
</body>
</html>"""

# Generate project cards
cards = ""
for project in os.listdir(projects_folder):
    project_path = os.path.join(projects_folder, project)
    if os.path.isdir(project_path):
        # Use folder name as project title
        project_name = project.replace("_", " ").title()
        # Paths
        project_page = f"{projects_folder}/{project}/index.html"
        github_link = f"https://github.com/yourusername/{project}"
        cards += f"""
<div class="project-card">
<h2>{project_name}</h2>
<p>A short description of {project_name}.</p>
<a href="{project_page}" target="_blank">View Project</a>
<a href="{github_link}" target="_blank">View Code</a>
</div>
"""

# Write index.html
with open(output_file, "w") as f:
    f.write(html_start + cards + html_end)

print(f"index.html updated with {len(os.listdir(projects_folder))} projects!")
