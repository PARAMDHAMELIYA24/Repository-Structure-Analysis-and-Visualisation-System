import database
from git import Repo
import shutil
from radon.complexity import cc_visit

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

    for file_path in file_list:

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

                files.append(
                    os.path.join(root, file)
                )

    return {
        "files": files
    }

@app.get("/api/stats")
def get_stats():

    graph = scan_project(CURRENT_DIRECTORY)

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

    return {

        "total_files":
            total_files,

        "total_loc":
            total_loc,

        "total_dependencies":
            total_dependencies,

        "most_complex_file":
            most_complex_file["id"]

    }

@app.get("/api/analyze/{file_id}")
def analyze_file(file_id: str):

    client = genai.Client(
        api_key=os.getenv("GEMINI_API_KEY")
    )

    if file_id in AI_CACHE:

        return {
            "summary": AI_CACHE[file_id]
        }

    code_text = ""

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

                code_text = f.read()

            break

    if not code_text:

        raise HTTPException(
            404,
            "File not found"
        )

    prompt = (
        "Explain what this code does in 3 simple sentences:\n\n"
        + code_text
    )

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    AI_CACHE[file_id] = response.text

    return {
        "summary": response.text
    }

@app.post("/api/chat")
def chat_with_repo(data: dict):

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

    repo_url = data["url"]

    clone_path = "temp_repo"

    if os.path.exists(clone_path):

        shutil.rmtree(clone_path)

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

 