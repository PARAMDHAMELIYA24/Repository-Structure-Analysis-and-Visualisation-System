import { toPng } from "html-to-image";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";
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
  const [stats, setStats] = useState({});
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [repoUrl, setRepoUrl] = useState("");
  const [cloneMessage, setCloneMessage] = useState("");
  const graphRef = useRef(null);

    useEffect(() => {

    fetch("http://localhost:8000/api/map")
        .then((response) => response.json())
        .then((data) => {

            setNodes(data.nodes);
            setEdges(data.edges);

        fetch("http://localhost:8000/api/files")
            .then((response) => response.json())
            .then((data) => {

                setFiles(data.files);
        
        fetch("http://localhost:8000/api/stats")
            .then((response) => response.json())
            .then((data) => {

                setStats(data);

        });

        });

    });

        

    }, []);

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

    setCloneMessage(

        data.message

    );

    window.location.reload(); 

};

  return (
    <div
      style={{
        width: "100vw",
        height: "100vh",
        display: "flex",
      }}
    >
      <div
  style={{
    width: "15%",
    padding: "15px",
    borderRight: "1px solid gray",
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
                flexDirection: "column"
            }}
      >
        <input
            placeholder="Search files..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{
                padding: "10px",
                margin: "10px",
                fontSize: "16px"
            }}
        />
        <button
    onClick={exportGraph}
    style={{
        margin: "10px",
        padding: "10px",
        fontSize: "16px"
    }}
>

    Export Architecture

</button>
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
        </ReactFlow>
      </div>

      <div
        style={{
          width: "25%",
          padding: "20px",
          borderLeft: "1px solid gray",
          overflowY: "auto",
        }}
      >
      <h2>AI Summary</h2>

      <p>{summary}</p>
      
      <hr />
      
      <h2>Source Code</h2>
      
      <SyntaxHighlighter
        language="python"
        style={vscDarkPlus}
        >
        {code}
       </SyntaxHighlighter>
       <hr />

       <hr />

<h2>GitHub Repository Analyzer</h2>

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

        marginBottom: "10px"

    }}

/>

<button

    onClick={analyzeRepo}

    style={{

        padding: "10px",

        marginBottom: "10px"

    }}

>

Analyze Repository

</button>

<p>

{cloneMessage}

</p>

<hr />

<h2>Repository AI Chat</h2>

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
        marginBottom: "10px"
    }}
/>

<button
    onClick={askAI}
    style={{
        padding: "10px",
        marginBottom: "10px"
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