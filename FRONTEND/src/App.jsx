import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend
} from "chart.js";

import { Pie } from "react-chartjs-2";

ChartJS.register(
  ArcElement,
  Tooltip,
  Legend
);
import { toPng } from "html-to-image";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";
import { oneLight }
from "react-syntax-highlighter/dist/esm/styles/prism";
import CustomNode from "./CustomNode";
import { useEffect, useState, useRef } from "react";
import { ReactFlow, MiniMap, Controls, Background } from "@xyflow/react";
import "@xyflow/react/dist/style.css";
const nodeTypes = {
  default: CustomNode
};


function App() {
  const [nodes, setNodes] = useState([]);
  const [edges, setEdges] = useState([]);
  const [summary, setSummary] = useState(
    "Click a file to generate an AI summary."
  );

  const [code, setCode] = useState("");
  const [search, setSearch] = useState("");
  const [files, setFiles] = useState([]);
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [repoUrl, setRepoUrl] = useState("");
  const [cloneMessage, setCloneMessage] = useState("");
  const [loadingRepo, setLoadingRepo] = useState(false);
  const [searchText, setSearchText] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [darkMode, setDarkMode] = useState(

    localStorage.getItem("darkMode") === "true"

    );
  const [stats, setStats] = useState({
  total_files: 0,
  total_loc: 0,
  total_dependencies: 0,
  complexity_distribution: {
    A: 0,
    B: 0,
    C: 0,
    D: 0
    }
    });
  const graphRef = useRef(null);

    useEffect(() => {

    fetch("http://localhost:8000/api/map")
        .then((response) => response.json())
        .then((data) => {

            setNodes(data.nodes);
            setEdges(data.edges);

        });

        fetch("http://localhost:8000/api/stats")
            .then((response) => response.json())
            .then((data) => {

                setStats(data);

            });

        fetch("http://localhost:8000/api/files")
            .then((response) => response.json())
            .then((data) => {

                setFiles(data.files);

        });
        
        fetch("http://localhost:8000/api/stats")
            .then((response) => response.json())
            .then((data) => {

                setStats(data);

        });

        

    }, []);

        useEffect(() => {

            localStorage.setItem(

                "darkMode",

                darkMode

            );

        }, [darkMode]);

  const onNodeClick = async (_, node) => {

  setSummary("Generating summary...");
  setCode("Loading code...");

  try {

    const summaryResponse =
      await fetch(
        `http://localhost:8000/api/analyze/${node.id}`
      );

    const summaryData =
      await summaryResponse.json();

    setSummary(
      summaryData.summary
    );

    const codeResponse =
      await fetch(
        `http://localhost:8000/api/code/${node.id}`
      );

    const codeData =
      await codeResponse.json();

    setCode(
      codeData.code
    );

  }

  catch (error) {

    console.error(error);

  }

};
const exportGraph = () => {

    if (!graphRef.current) {

        return;

    }

    toPng(graphRef.current)

        .then((dataUrl) => {

            const link = document.createElement("a");

            link.download = "architecture.png";

            link.href = dataUrl;

            link.click();

        });

};

const askAI = async () => {

    const response = await fetch(

        "http://localhost:8000/api/chat",

        {

            method: "POST",

            headers: {

                "Content-Type":

                "application/json"

            },

            body: JSON.stringify({

                question

            })

        }

    );

    const data = await response.json();

    setAnswer(

        data.answer

    );

};

const analyzeRepo = async () => {

    setLoadingRepo(true);

    setCloneMessage(
        "Analyzing repository..."
    );

    try {

        console.log("Starting clone...");
        const response = await fetch(

            "http://localhost:8000/api/clone",

            {

                method: "POST",

                headers: {

                    "Content-Type":
                        "application/json"

                },

                body: JSON.stringify({

                    url: repoUrl

                })

            }

        );

        const data = await response.json();
        console.log("Clone finished");

        setCloneMessage(
            data.message
        );

        window.location.reload();

    }

    catch (error) {

        setCloneMessage(
            "Failed to analyze repository"
        );

    }

    finally {

        setLoadingRepo(false);

    }

};

const pieData = {
  labels: [
    "Simple (A)",
    "Moderate (B)",
    "Complex (C)",
    "Very Complex (D)"
  ],

  datasets: [
    {
      data: [
        stats.complexity_distribution.A,
        stats.complexity_distribution.B,
        stats.complexity_distribution.C,
        stats.complexity_distribution.D
      ],

      backgroundColor: [
        "#4CAF50",   // green
        "#FFC107",   // yellow
        "#FF9800",   // orange
        "#F44336"    // red
      ],

      borderWidth: 1
    }
  ]
};

const pieOptions = {

  plugins: {

    legend: {

      position: "bottom",

      labels: {

        color:

          darkMode

          ? "white"

          : "black",

        font: {

          size: 14

        }

      }

    }

  }

};

const downloadReport = () => {

    window.open(

        "http://localhost:8000/api/report"

    );

};

const searchRepository = async () => {

    if (!searchText) {

        return;

    }

    const response = await fetch(

        `http://localhost:8000/api/search?query=${searchText}`

    );

    const data = await response.json();

    setSearchResults(

        data.results

    );

};

  return (
    <div
  style={{

    width: "100vw",

    height: "100vh",

    display: "flex",

    backgroundColor:

      darkMode

      ? "#0f172a"

      : "#f5f5f5",

        color:

      darkMode

      ? "white"

      : "black"

        }}
    >
      <div
  style={{
    width: "15%",
    padding: "15px",
    borderLeft:

    darkMode

    ? "1px solid white"

    : "1px solid black",
    overflowY: "auto"
  }}
>

<h2>Files</h2>

<hr />

<h3>Project Stats</h3>

<p>

Files:
{stats.total_files}

</p>

<p>

LOC:
{stats.total_loc}

</p>

<p>

Dependencies:
{stats.total_dependencies}

</p>

<p>

Complex File:
{stats.most_complex_file}

</p>

<hr />

{
files.map((file) => (

<div
    key={file}
    style={{
        marginBottom: "10px",
        cursor: "pointer"
    }}
>
    {file}
</div>

))
}

</div>
        
      <div
            ref={graphRef}
            style={{
                width: "60%",
                height: "100%",
                display: "flex",
                flexDirection: "column",
                color: "black"
                
            }}
      >

        <button

    onClick={() =>

        setDarkMode(

            !darkMode

        )

    }

    style={{

    margin: "10px",

    padding: "10px",

    fontSize: "16px",

    backgroundColor:

        darkMode

        ? "#334155"

        : "#e5e7eb",

    color:

        darkMode

        ? "white"

        : "black"

}}

>

{

darkMode

? "☀️ Light Mode"

: "🌙 Dark Mode"

}

</button>
        <input
            placeholder="Search files..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{

    padding: "10px",

    margin: "10px",

    fontSize: "16px",

    backgroundColor:

        darkMode

        ? "#1e293b"

        : "white",

    color:

        darkMode

        ? "white"

        : "black"

}}
        />
<div
    style={{

        display: "flex",

        gap: "10px",

        margin: "10px"

    }}
>

    <button
        onClick={exportGraph}
        style={{

            padding: "10px",

            backgroundColor:

                darkMode

                ? "#334155"

                : "white",

            color:

                darkMode

                ? "white"

                : "black"

        }}
    >

        Export Architecture

    </button>

    <button
        onClick={downloadReport}
        style={{

            padding: "10px",

            backgroundColor:

                darkMode

                ? "#334155"

                : "white",

            color:

                darkMode

                ? "white"

                : "black"

        }}
    >

        Download PDF Report

    </button>

</div>


        <ReactFlow
            nodes={nodes}
            edges={edges}
            fitView
            onNodeClick={onNodeClick}
            nodeTypes={nodeTypes}
        >
          <MiniMap />
          <Controls />
          <Background />
          <div
    style={{

        display: "flex",

        gap: "20px",

        margin: "10px"

    }}
>

    <div>🟢 A : Simple</div>

    <div>🟡 B : Moderate</div>

    <div>🟠 C : Complex</div>

    <div>🔴 D : Very Complex</div>

</div>
        </ReactFlow>
      </div>

      <div
        style={{
          width: "25%",
          padding: "20px",
          borderLeft:

    darkMode

    ? "1px solid white"

    : "1px solid black",
          overflowY: "auto",
        }}
      >
      <h2
    style={{

        color:

            darkMode

            ? "white"

            : "black"

    }}
>
    AI Summary
</h2>

      <p>{summary}</p>
      
      <hr />
      
      <h2
    style={{

        color:

            darkMode

            ? "white"

            : "black"

    }}
>
    Source Code
</h2>
      
      <SyntaxHighlighter

    language="python"

    style={

        darkMode

        ? vscDarkPlus

        : oneLight

        

    }

>

    {code}

</SyntaxHighlighter>
       <hr />

       <hr />

       <hr />

<h2>Repository Search</h2>

<input

    value={searchText}

    onChange={(e) =>

        setSearchText(

            e.target.value

        )

    }

    placeholder="Search code..."

    style={{

        width: "100%",

        padding: "10px",

        marginBottom: "10px"

    }}

/>

<button

    onClick={searchRepository}

    style={{

        padding: "10px"

    }}

>

    Search

</button>

{

searchResults.map(

(result, index) => (

<div

    key={index}

    style={{

        marginTop: "15px",

        padding: "10px",

        border: "1px solid gray"

    }}

>

<b>

{result.file}

</b>

<br />

Line:

{result.line_number}

<br />

<code>

{result.content}

</code>

</div>

))

}

<h2
    style={{

        color:

            darkMode

            ? "white"

            : "black"

    }}
>
    GitHub Repository Analyzer
</h2>

<input

    value={repoUrl}

    onChange={(e) =>

        setRepoUrl(

            e.target.value

        )

    }

    placeholder="Enter GitHub URL"

    style={{

    width: "100%",

    padding: "10px",

    marginBottom: "10px",

    backgroundColor:

    darkMode

    ? "#334155"

    : "#e5e7eb",

    color:

        darkMode

        ? "white"

        : "black"

}}

/>

<button
    onClick={analyzeRepo}
    disabled={loadingRepo}
    style={{

        padding: "10px",

        marginBottom: "10px",

        backgroundColor:

            darkMode

            ? "#334155"

            : "#e5e7eb",

        color:

            darkMode

            ? "white"

            : "black"

    }}
>

{
    loadingRepo
        ? "Analyzing..."
        : "Analyze Repository"
}

</button>

{loadingRepo && (

<div
    style={{

        width: "40px",

        height: "40px",

        border: "5px solid gray",

        borderTop:
            "5px solid #4caf50",

        borderRadius: "50%",

        animation:
            "spin 1s linear infinite",

        margin:
            "10px auto"

    }}
>

</div>

)}

<p>

{cloneMessage}

</p>

<hr />

<hr />

<h2
    style={{

        color:

            darkMode

            ? "white"

            : "black"

    }}
>
    Project Statistics
</h2>

<p>

Files:

{stats.total_files}

</p>

<p>

Lines of Code:

{stats.total_loc}

</p>

<p>

Dependencies:

{stats.total_dependencies}

</p>

<Pie
  data={pieData}
  options={pieOptions}
/>

<hr />

<h2
    style={{

        color:

            darkMode

            ? "white"

            : "black"

    }}
>
    Repository AI Chat
</h2>

<input
    value={question}
    onChange={(e) =>
        setQuestion(
            e.target.value
        )
    }
    placeholder="Ask about the repository..."
    style={{

        width: "100%",

        padding: "10px",

        marginBottom: "10px",

        backgroundColor:

    darkMode

    ? "#334155"

    : "#e5e7eb",

        color:

            darkMode

            ? "white"

            : "black"

    }}
/>

<button
    onClick={askAI}
    style={{

        padding: "10px",

        marginBottom: "10px",

        backgroundColor:

            darkMode

            ? "#334155"

            : "#e5e7eb",

        color:

            darkMode

            ? "white"

            : "black"

    }}
>

    Ask AI

</button>

<p>

    {answer}

</p>
      </div>
    </div>
  );
}

export default App;