## Info
- These instructions are needed to demonstrate the ability to convert raw JSONs data from GitHub Copilot telemetry into a CSV file that is easy to analyze and easy to open in Excel.

## How to ask for demo in chat
Use this case to make demo:
```
Show me demo from file:
Please process all github copilot telemetry data in `work\telemetry`. 
```

## Important
- Follow instructions to enable `MCP`, then use `MCP` for calling all the tools bellow. If `MCP` is not avaliable - ask user to run it and stop.
- Workspace is `mcp_server/projects/telemetry/`.
- Please use `./pipeline/telemetry.json` pipeline to process all the files. 
- Don't analyze all the files that make up the essence of this transformation — just call the pipeline with `lng_batch_run` tool.
- You can use `{"pipeline_file": "mcp_server/projects/telemetry/pipeline/telemetry.json", "user_params": {"base_directory": "<base_directory>"}}` to run the pipeline.
- `<base_directory>` directory must be the one selected by the user.
- The pipeline will generate both CSV report and Excel report using the template in `<base_directory>/out/` folder.
- You can check the statistics of the generated file using `lng_xls_batch` with the `analyze` parameter. 