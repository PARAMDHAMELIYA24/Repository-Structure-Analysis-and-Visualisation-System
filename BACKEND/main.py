import database
import tempfile
from git import Repo
import shutil
from radon.complexity import cc_visit
from fastapi.responses import FileResponse

from reportlab.platypus import (

    SimpleDocTemplate,

    Paragraph,

    Spacer,

    Table

)
from reportlab.platypus import Table
from reportlab.lib.styles import getSampleStyleSheet
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from google import genai
import os
import ast




load_dotenv()


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

AI_CACHE = {}
CHAT_HISTORY = []
CURRENT_DIRECTORY = None


def scan_project(directory):
    nodes = []
    edges = []
    file_list = []
    edge_set = set()

    x = 0
    y = 0

    extensions = (
        ".py",
        ".cpp",
        ".c",
        ".h",
        ".hpp",
        ".js",
        ".jsx",
        ".ts",
        ".java"
    )

    for root, dirs, files in os.walk(directory):

        dirs[:] = [

    d

    for d in dirs

    if d not in (

        "venv",

        "__pycache__",

        "node_modules",

        ".git",

        "tests",

        "docs"

    )

]

        if (
            "venv" in root
            or "__pycache__" in root
            or "node_modules" in root
            or ".git" in root
        ):
            continue

        for file in files:

            if file.endswith(extensions):

                file_list.append(
                    os.path.join(root, file)
                )

    for file_path in file_list[:300]:


        file_name = os.path.basename(file_path)

        function_count = 0
        import_count = 0
        complexity = "A"

        try:

            with open(
                file_path,
                "r",
                encoding="utf-8"
            ) as f:

                lines = f.readlines()

            loc = len(lines)

            code_text = "".join(lines)

            # Complexity calculation
            try:

                results = cc_visit(code_text)

                if results:

                    max_complexity = max(
                        item.complexity
                        for item in results
                    )

                    if max_complexity <= 5:

                        complexity = "A"

                    elif max_complexity <= 10:

                        complexity = "B"

                    elif max_complexity <= 20:

                        complexity = "C"

                    else:

                        complexity = "D"

            except:

                pass

            # Count functions and imports
            try:

                tree = ast.parse(code_text)

                for node in ast.walk(tree):

                    if isinstance(
                        node,
                        ast.FunctionDef
                    ):

                        function_count += 1

                    if isinstance(
                        node,
                        (
                            ast.Import,
                            ast.ImportFrom
                        )
                    ):

                        import_count += 1

            except:

                pass

        except:

            lines = []
            loc = 0

        nodes.append({
            "id": file_name,
            "data": {
                "label": file_name,
                "loc": loc,
                "path": file_path,
                "functions": function_count,
                "imports": import_count,
                "complexity": complexity
            },
            "position": {
                "x": x,
                "y": y
            }
        })

        x += 250

        if x > 1000:

            x = 0
            y += 150

        for line in lines:

            line = line.strip()

            if (
                line.startswith("import ")
                or line.startswith("from ")
            ):

                for other_path in file_list:

                    other_name = os.path.basename(
                        other_path
                    )

                    module_name = (
                        other_name.replace(
                            ".py",
                            ""
                        )
                    )

                    if (
                        module_name in line
                        and other_name != file_name
                    ):

                        edge_id = (
                            f"{file_name}-{other_name}"
                        )

                        if edge_id not in edge_set:

                            edge_set.add(edge_id)

                            edges.append({
                                "id": edge_id,
                                "source": file_name,
                                "target": other_name
                            })

    return {
        "nodes": nodes,
        "edges": edges
    }

@app.get("/api/map")
def get_map():

    if CURRENT_DIRECTORY is None:

        return {

            "nodes": [],

            "edges": []

        }

    return scan_project(
        CURRENT_DIRECTORY
    )

@app.get("/")
def home():
    return {"message": "Server is running"}

@app.get("/test-gemini")
def test_gemini():
    try:
        client = genai.Client(
            api_key=os.getenv("GEMINI_API_KEY")
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents="Say hello in one sentence."
        )

        return {
            "response": response.text
        }

    except Exception as e:
        return {
            "error": str(e)
        }

@app.get("/test-scan")
def test_scan():
    return scan_project(CURRENT_DIRECTORY)


@app.get("/api/code/{file_id}")
def get_code(file_id: str):

    if CURRENT_DIRECTORY is None:

        raise HTTPException(
            404,
            "No repository loaded"
        )

    for root, dirs, files in os.walk(CURRENT_DIRECTORY):

        if (
            "venv" in root
            or "node_modules" in root
        ):
            continue

        if file_id in files:

            with open(
                os.path.join(root, file_id),
                "r",
                encoding="utf-8"
            ) as f:

                return {
                    "code": f.read()
                }

    raise HTTPException(
        404,
        "File not found"
    )

@app.get("/api/files")
def get_files():

    if CURRENT_DIRECTORY is None:

        return {

            "files": []

        }

    files = []

    extensions = (
        ".py",
        ".cpp",
        ".c",
        ".h",
        ".hpp",
        ".js",
        ".jsx",
        ".ts",
        ".java"
    )

    for root, dirs, files in os.walk(CURRENT_DIRECTORY):

        if (
            "venv" in root
            or "__pycache__" in root
            or "node_modules" in root
            or ".git" in root
        ):
            continue

        for file in files:

            if file.endswith(extensions):

                if len(files) < 300:

                    files.append(
                        os.path.join(root, file)
                    )

    return {
        "files": files
    }

@app.get("/api/stats")
def get_stats():

    if CURRENT_DIRECTORY is None:

        return {
            "total_files": 0,
            "total_loc": 0,
            "total_dependencies": 0,
            "most_complex_file": "",
            "complexity_distribution": {
                "A": 0,
                "B": 0,
                "C": 0,
                "D": 0
            }
        }

    graph = scan_project(CURRENT_DIRECTORY)

    total_files = len(graph["nodes"])

    total_loc = sum(
        node["data"]["loc"]
        for node in graph["nodes"]
    )

    total_dependencies = len(graph["edges"])

    count_A = 0
    count_B = 0
    count_C = 0
    count_D = 0

    for node in graph["nodes"]:

        complexity = node["data"]["complexity"]

        if complexity == "A":
            count_A += 1

        elif complexity == "B":
            count_B += 1

        elif complexity == "C":
            count_C += 1

        else:
            count_D += 1

    complexity_rank = {
        "A": 1,
        "B": 2,
        "C": 3,
        "D": 4
    }

    most_complex_file = max(
        graph["nodes"],
        key=lambda node:
        complexity_rank[node["data"]["complexity"]]
    )

    return {

        "total_files": total_files,

        "total_loc": total_loc,

        "total_dependencies": total_dependencies,

        "most_complex_file": most_complex_file["id"],

        "complexity_distribution": {

            "A": count_A,
            "B": count_B,
            "C": count_C,
            "D": count_D

        }

    }

@app.get("/api/report")
def generate_report():

    graph = scan_project(

        CURRENT_DIRECTORY or "."

    )

    total_files = len(
        graph["nodes"]
    )

    total_loc = sum(

        node["data"]["loc"]

        for node in graph["nodes"]

    )

    total_dependencies = len(
        graph["edges"]
    )

    complexity_rank = {

        "A": 1,
        "B": 2,
        "C": 3,
        "D": 4

    }

    most_complex_file = max(

        graph["nodes"],

        key=lambda node:

        complexity_rank[
            node["data"]["complexity"]
        ]

    )

    largest_files = sorted(

        graph["nodes"],

        key=lambda node:
        node["data"]["loc"],

        reverse=True

    )[:10]

    filename = "project_report.pdf"

    doc = SimpleDocTemplate(
        filename
    )

    styles = getSampleStyleSheet()

    story = []

    story.append(

        Paragraph(

            "Repository Analysis Report",

            styles["Title"]

        )

    )

    story.append(
        Spacer(1, 20)
    )

    story.append(

        Paragraph(

            "Project Statistics",

            styles["Heading2"]

        )

    )

    data = [

        ["Metric", "Value"],

        ["Total Files",
         str(total_files)],

        ["Total LOC",
         str(total_loc)],

        ["Dependencies",
         str(total_dependencies)],

        ["Most Complex File",
         most_complex_file["id"]]

    ]

    story.append(
        Table(data)
    )

    story.append(
        Spacer(1, 20)
    )

    story.append(

        Paragraph(

            "Top 10 Largest Files",

            styles["Heading2"]

        )

    )

    for node in largest_files:

        story.append(

            Paragraph(

                f'{node["id"]} : {node["data"]["loc"]} LOC',

                styles["BodyText"]

            )

        )

    story.append(
        Spacer(1, 20)
    )

    story.append(

        Paragraph(

            "Complexity Distribution",

            styles["Heading2"]

        )

    )

    count_A = sum(

        1

        for node in graph["nodes"]

        if node["data"]["complexity"] == "A"

    )

    count_B = sum(

        1

        for node in graph["nodes"]

        if node["data"]["complexity"] == "B"

    )

    count_C = sum(

        1

        for node in graph["nodes"]

        if node["data"]["complexity"] == "C"

    )

    count_D = sum(

        1

        for node in graph["nodes"]

        if node["data"]["complexity"] == "D"

    )

    story.append(

        Paragraph(

            f"Grade A Files : {count_A}",

            styles["BodyText"]

        )

    )

    story.append(

        Paragraph(

            f"Grade B Files : {count_B}",

            styles["BodyText"]

        )

    )

    story.append(

        Paragraph(

            f"Grade C Files : {count_C}",

            styles["BodyText"]

        )

    )

    story.append(

        Paragraph(

            f"Grade D Files : {count_D}",

            styles["BodyText"]

        )

    )

    doc.build(
        story
    )

    return FileResponse(

        filename,

        media_type="application/pdf",

        filename="project_report.pdf"

    )

@app.post("/api/chat")
def chat_with_repo(data: dict):

    if CURRENT_DIRECTORY is None:

        return {

        "answer":
        "Please analyze a repository first."

        }

    question = data["question"]

    repo_text = ""

    extensions = (
        ".py",
        ".cpp",
        ".c",
        ".h",
        ".hpp",
        ".js",
        ".jsx",
        ".ts",
        ".java"
    )

    for root, dirs, files in os.walk(CURRENT_DIRECTORY):

        if (
            "venv" in root
            or "__pycache__" in root
            or "node_modules" in root
            or ".git" in root
        ):
            continue

        for file in files:

            if file.endswith(extensions):

                try:

                    with open(
                        os.path.join(root, file),
                        "r",
                        encoding="utf-8"
                    ) as f:

                        repo_text += (

                            "\n\nFILE: "

                            + file

                            + "\n"

                            + + f.read()[:2000]

                        )

                except:

                    pass

    client = genai.Client(
        api_key=os.getenv(
            "GEMINI_API_KEY"
        )
    )

    prompt = (

        "Repository contents:\n\n"

        + repo_text

        + "\n\nQuestion:\n"

        + question

    )

    response = client.models.generate_content(

        model="gemini-2.5-flash",

        contents=prompt

    )

    return {

        "answer": response.text

    }

@app.post("/api/clone")
def clone_repo(data: dict):

    global CURRENT_DIRECTORY

    import tempfile
    import uuid

    repo_url = data["url"]

    clone_path = os.path.join(

        tempfile.gettempdir(),

        "repo_analyzer_temp_" +

        str(uuid.uuid4())[:8]

    )

    Repo.clone_from(

        repo_url,

        clone_path

    )

    CURRENT_DIRECTORY = clone_path

    AI_CACHE.clear()

    CHAT_HISTORY.clear()

    return {

        "message":

        "Repository cloned successfully"

    }

@app.get("/api/search")
def search_code(query: str):

    results = []

    directory = CURRENT_DIRECTORY or "."

    extensions = (
        ".py",
        ".cpp",
        ".c",
        ".h",
        ".hpp",
        ".js",
        ".jsx",
        ".ts",
        ".java"
    )

    for root, dirs, files in os.walk(directory):

        if (
            "venv" in root
            or "__pycache__" in root
            or "node_modules" in root
            or ".git" in root
        ):
            continue

        for file in files:

            if file.endswith(extensions):

                path = os.path.join(root, file)

                try:

                    with open(
                        path,
                        "r",
                        encoding="utf-8"
                    ) as f:

                        lines = f.readlines()

                    for i, line in enumerate(lines):

                        if query.lower() in line.lower():

                            results.append({

                                "file": file,

                                "line_number": i + 1,

                                "content": line.strip()

                            })

                except:

                    pass

    return {

        "results": results

    }

@app.get("/api/history")
def get_history():

    repo_path = CURRENT_DIRECTORY or "."

    try:

        repo = Repo(repo_path)

    except:

        return {

            "total_commits": 0,

            "contributors": [],

            "latest_commit": "",

            "history": []

        }

    commits = list(repo.iter_commits())

    contributor_count = {}

    history = []

    for commit in commits[:20]:

        author = commit.author.name

        contributor_count[author] = (

            contributor_count.get(author, 0)

            + 1

        )

        history.append({

            "author": author,

            "message": commit.message.strip(),

            "date": str(commit.committed_datetime)

        })

    contributors = [

        {

            "name": name,

            "commits": count

        }

        for name, count

        in contributor_count.items()

    ]

    contributors.sort(

        key=lambda x: x["commits"],

        reverse=True

    )

    latest_commit = (

        commits[0].message.strip()

        if commits

        else ""

    )

    return {

        "total_commits": len(commits),

        "contributors": contributors,

        "latest_commit": latest_commit,

        "history": history

    }