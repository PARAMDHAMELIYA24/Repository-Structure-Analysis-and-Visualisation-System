function CustomNode({ data }) {

    let backgroundColor = "#90EE90";

    if (data.complexity === "B") {

        backgroundColor = "#FFFF99";

    }

    if (data.complexity === "C") {

        backgroundColor = "#FFD580";

    }

    if (data.complexity === "D") {

        backgroundColor = "#FF9999";

    }

    return (

        <div
            style={{
                backgroundColor: backgroundColor,
                padding: "15px",
                border: "1px solid black",
                borderRadius: "10px",
                width: "170px",
                textAlign: "center"
            }}
        >

            <strong>

                {data.label}

            </strong>

            <hr />

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