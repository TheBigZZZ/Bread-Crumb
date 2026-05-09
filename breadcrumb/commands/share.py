"""
Export chat sessions as shareable HTML.
"""

from pathlib import Path
from typing import List, Dict
from rich.console import Console

console = Console()


def generate_html(title: str, messages: List[Dict]) -> str:
    """Generate beautiful HTML from chat messages."""
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 20px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 32px;
            margin-bottom: 10px;
        }}
        
        .header p {{
            opacity: 0.9;
            font-size: 14px;
        }}
        
        .messages {{
            padding: 30px;
            max-height: 70vh;
            overflow-y: auto;
        }}
        
        .message {{
            margin-bottom: 20px;
            animation: fadeIn 0.3s ease-in;
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        .message.user {{
            text-align: right;
        }}
        
        .message.user .content {{
            background: #667eea;
            color: white;
            margin-left: 20%;
        }}
        
        .message.assistant .content {{
            background: #f0f0f0;
            color: #333;
            margin-right: 20%;
        }}
        
        .role {{
            font-size: 12px;
            font-weight: 600;
            margin-bottom: 5px;
            opacity: 0.7;
            text-transform: uppercase;
        }}
        
        .content {{
            padding: 12px 16px;
            border-radius: 8px;
            line-height: 1.5;
            word-wrap: break-word;
        }}
        
        .content code {{
            background: rgba(0, 0, 0, 0.1);
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Monaco', 'Courier New', monospace;
            font-size: 13px;
        }}
        
        .content pre {{
            background: rgba(0, 0, 0, 0.05);
            padding: 10px;
            border-radius: 5px;
            overflow-x: auto;
            margin: 10px 0;
        }}
        
        .content pre code {{
            background: none;
            padding: 0;
        }}
        
        .footer {{
            padding: 20px;
            background: #f9f9f9;
            text-align: center;
            font-size: 12px;
            color: #999;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🍞 Bread Crumb Chat</h1>
            <p>{title}</p>
        </div>
        
        <div class="messages">
"""

    for msg in messages:
        role = msg.get("role", "unknown")
        content = msg.get("content", "").replace("<", "&lt;").replace(">", "&gt;")
        
        html += f"""            <div class="message {role}">
                <div class="role">{role}</div>
                <div class="content">{content}</div>
            </div>
"""

    html += f"""        </div>
        
        <div class="footer">
            <p>Powered by Bread Crumb</p>
            <p>Generated on {Path.cwd()}</p>
        </div>
    </div>
</body>
</html>"""

    return html


def cmd_share(session_file: Path, output_file: Optional[Path] = None) -> Optional[Path]:
    """
    Export a chat session as shareable HTML.
    
    Args:
        session_file: Path to session JSON file
        output_file: Where to save the HTML (default: session.html)
    
    Returns:
        Path to created HTML file
    """
    import json
    
    if not session_file.exists():
        console.print(f"[red]Session file not found: {session_file}[/red]")
        return None
    
    try:
        data = json.loads(session_file.read_text())
        messages = data.get("messages", [])
    except Exception as e:
        console.print(f"[red]Error reading session: {e}[/red]")
        return None
    
    title = f"Bread Crumb Chat - {data.get('session', 'default')}"
    html = generate_html(title, messages)
    
    if not output_file:
        output_file = session_file.parent / f"{session_file.stem}.html"
    
    try:
        output_file.write_text(html)
        console.print(f"[green]✓ Exported to {output_file}[/green]")
        return output_file
    except Exception as e:
        console.print(f"[red]Error writing HTML: {e}[/red]")
        return None
