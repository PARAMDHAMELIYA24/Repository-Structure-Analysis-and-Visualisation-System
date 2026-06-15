function CustomNode({ data }) {

    let backgroundColor = "#22c55e";

    if (data.complexity === "B") {

        backgroundColor = "#eab308";

    }

    else if (data.complexity === "C") {

        backgroundColor = "#f97316";

    }

    else if (data.complexity === "D") {

        backgroundColor = "#ef4444";

    }

    return (

        <div
            style={{

                backgroundColor,

                padding: "15px",

                borderRadius: "12px",

                width: "170px",

                border: "2px solid black",

                color: "black",

                fontSize: "13px"

            }}
        >

            <b>{data.label}</b>

            <br />

            LOC: {data.loc}

            <br />

            Functions: {data.functions}

            <br />

            Imports: {data.imports}

            <br />

            Complexity: {data.complexity}

        </div>

    );

}

export default CustomNode;