import os
import json
import base64

def main():
    workspace_dir = r"D:\github\laboratory\PromptWars_May2026"
    repo_root = r"D:\github\laboratory"
    
    # Read files
    files_to_bundle = {
        "app.py": os.path.join(workspace_dir, "app.py"),
        "src/__init__.py": os.path.join(workspace_dir, "src", "__init__.py"),
        "src/models.py": os.path.join(workspace_dir, "src", "models.py"),
        "src/database.py": os.path.join(workspace_dir, "src", "database.py"),
        "src/planner.py": os.path.join(workspace_dir, "src", "planner.py"),
        "src/replanner.py": os.path.join(workspace_dir, "src", "replanner.py"),
        "src/utils.py": os.path.join(workspace_dir, "src", "utils.py"),
        ".streamlit/config.toml": os.path.join(workspace_dir, ".streamlit", "config.toml"),
    }
    
    files_content = {}
    for virtual_path, local_path in files_to_bundle.items():
        if os.path.exists(local_path):
            with open(local_path, "r", encoding="utf-8") as f:
                files_content[virtual_path] = f.read()
        else:
            # If __init__.py doesn't exist, write empty string
            files_content[virtual_path] = ""
            
    # Serialize to JSON and encode in Base64
    json_bytes = json.dumps(files_content).encode('utf-8')
    b64_string = base64.b64encode(json_bytes).decode('utf-8')
    
    # Generate HTML content with beautiful modern White and Navy Blue spinner overlay
    html_content = f"""<!DOCTYPE html>
<html>
  <head>
    <meta charset="UTF-8" />
    <meta http-equiv="X-UA-Compatible" content="IE=edge" />
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no" />
    <title>VoyageFlow | Dynamic Travel Planner</title>
    
    <!-- Google Fonts Outfit -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    
    <link
      rel="stylesheet"
      href="https://cdn.jsdelivr.net/npm/@stlite/browser@0.62.1/build/stlite.css"
    />
    <style>
      body, html {{
        margin: 0;
        padding: 0;
        width: 100%;
        height: 100%;
        font-family: 'Outfit', sans-serif;
        background-color: #FFFFFF;
      }}
      #root {{
        width: 100%;
        height: 100%;
      }}
      
      /* Premium Loading Spinner Screen overlay */
      #loading-screen {{
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: #FFFFFF;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        z-index: 99999;
        transition: opacity 0.5s ease;
      }}
      
      .spinner {{
        width: 50px;
        height: 50px;
        border: 5px solid rgba(11, 27, 61, 0.1);
        border-top: 5px solid #0B1B3D;
        border-radius: 50%;
        animation: spin 1s linear infinite;
        margin-bottom: 20px;
      }}
      
      .loading-title {{
        font-size: 24px;
        font-weight: 700;
        color: #0B1B3D;
        margin: 0 0 10px 0;
        letter-spacing: 1px;
      }}
      
      .loading-subtitle {{
        font-size: 14px;
        color: #475569;
        margin: 0;
      }}
      
      @keyframes spin {{
        0% {{ transform: rotate(0deg); }}
        100% {{ transform: rotate(360deg); }}
      }}
    </style>
  </head>
  <body>
    <div id="loading-screen">
      <div class="spinner"></div>
      <h2 class="loading-title">VOYAGEFLOW</h2>
      <p class="loading-subtitle">Initializing In-Browser AI Engine | Prompt Wars May 2026 Submission by Ankit Mathur</p>
    </div>
    
    <div id="root"></div>
    
    <script type="module">
      import {{ mount }} from "https://cdn.jsdelivr.net/npm/@stlite/browser@0.62.1/build/stlite.js";
      
      // Decode the files from Base64
      const filesB64 = "{b64_string}";
      const filesJson = atob(filesB64);
      const files = JSON.parse(filesJson);
      
      mount(
        {{
          requirements: ["pandas", "plotly", "pydeck", "pydantic==1.10.12"],
          entrypoint: "app.py",
          files: files,
          style: {{
            base: "light",
            primaryColor: "#1E3A8A",
            backgroundColor: "#FFFFFF",
            secondaryBackgroundColor: "#F8FAFC",
            textColor: "#0B1B3D"
          }}
        }},
        document.getElementById("root")
      ).then(() => {{
        // Fade out and remove loading screen once application mounts successfully
        const loader = document.getElementById("loading-screen");
        loader.style.opacity = "0";
        setTimeout(() => {{
          loader.remove();
        }}, 500);
      }});
    </script>
  </body>
</html>
"""

    output_path = os.path.join(repo_root, "index.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    print(f"Successfully generated stlite index.html at {output_path}!")

if __name__ == "__main__":
    main()
