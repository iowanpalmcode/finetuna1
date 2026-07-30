# AI Agent UI - Web Interface

A beautiful, interactive web-based user interface for the AI Agent Framework with drag-and-drop trait management.

## Features

✨ **Drag & Drop Interface** - Intuitively drag personality traits and drop them onto your agent

🎨 **Beautiful UI** - Modern, responsive design with gradient backgrounds and smooth animations

🤖 **Real-time Generation** - Instantly generate responses with personality-modified text

📊 **Personality Profiles** - View detailed behavioral summaries with active traits

🔄 **Live Preview** - See side-by-side comparison of original vs personality-modified responses

## Installation

### Step 1: Install Flask

```bash
pip install -r requirements.txt
```

Or manually:
```bash
pip install flask
```

### Step 2: Run the Server

From the project directory:

```bash
python ui_server.py
```

You should see:
```
===============================================================================
AI Agent Framework - Web UI Server
===============================================================================

🚀 Starting server...
📱 Open your browser and go to: http://localhost:5000

Press Ctrl+C to stop the server.

===============================================================================
```

### Step 3: Open in Browser

Open your web browser and navigate to:
```
http://localhost:5000
```

## How to Use

### 1. Create an Agent

- Enter a name for your agent in the "Your Agent" section
- Click **Create Agent** button
- Your agent is now ready to receive personality traits

### 2. Add Traits (Drag & Drop)

- Look at the "Available Emotions & Traits" section on the left
- **Click and drag** any trait (e.g., 🧠 Smart, 😊 Happy, 🎨 Creative)
- **Drop it** into the drop zone labeled "Drag traits here"
- The trait will be added to your agent and appear in the personality profile

### 3. Build Your Personality

Keep dragging and dropping traits to create unique personality combinations:
- **Technical Advisor**: Smart + Analytical + Efficient
- **Creative Partner**: Creative + Curious + Happy
- **Empathetic Helper**: Empathetic + Happy + Curious
- **Lazy Genius**: Lazy + Smart + Efficient

### 4. Generate Response

- Enter a base response or prompt in the "Generate Response" text box
- Example: "I will help you with this task."
- Click **Generate Personality Response**
- See how your agent's personality transforms the response!

### 5. View Results

The output shows:
- **Original**: Your unmodified text
- **With Personality**: The text transformed by your agent's traits
- **Active Traits**: The traits that influenced the response

## Available Traits

| Emoji | Trait | Description |
|-------|-------|-------------|
| 🧠 | Smart | Intellectually capable, analytical |
| 😊 | Happy | Positive, optimistic outlook |
| 🎨 | Creative | Imaginative, innovative |
| 🔍 | Curious | Inquisitive, loves exploration |
| ⚡ | Efficient | Optimizes output, minimizes waste |
| 😴 | Lazy | Prefers shortcuts, minimal effort |
| 😢 | Sad | Melancholic, reflective |
| 📊 | Analytical | Logical, data-driven |
| 🎲 | RiskTaking | Bold, adventurous |
| ❤️ | Empathetic | Compassionate, emotionally aware |

## Example Workflows

### Example 1: Create a Helpful AI

1. Create agent named "HelpfulBot"
2. Drag these traits: 😊 Happy, ❤️ Empathetic, 🧠 Smart
3. Enter prompt: "We can work on this problem."
4. Generate!

**Result**: The response becomes warmer and more supportive while maintaining intelligence.

### Example 2: Create a Lazy Genius

1. Create agent named "LazyGenius"
2. Drag these traits: 🧠 Smart, 😴 Lazy, ⚡ Efficient
3. Enter prompt: "You might want to consider this approach step by step."
4. Generate!

**Result**: The response becomes much more concise while staying intelligent.

### Example 3: Create a Creative Dreamer

1. Create agent named "CreativeDreamer"
2. Drag these traits: 🎨 Creative, 🔍 Curious, 😊 Happy
3. Enter prompt: "We could try something new."
4. Generate!

**Result**: The response becomes more imaginative and enthusiastic.

## Advanced Features

### Trait Intensity

Each trait has an intensity level (displayed as a percentage) that determines how strongly it influences responses. All dropped traits start at 70% intensity.

### Multiple Agents

You can create multiple agents by:
1. Entering a new name in the input field
2. Clicking **Create Agent** again
3. Each agent maintains its own personality profile

### Remove Traits

To remove a trait from your agent:
- Click the **×** button on any trait in the agent's trait list
- The trait will be removed and the personality profile will update

## API Endpoints

The UI uses these REST API endpoints:

```
GET  /api/traits                    # Get all available traits
POST /api/agents                    # Create new agent
POST /api/agents/{id}/traits        # Add trait to agent
DELETE /api/agents/{id}/traits/{name}  # Remove trait from agent
GET  /api/agents/{id}/profile       # Get agent profile
POST /api/agents/{id}/generate      # Generate response
```

## Troubleshooting

### Server won't start

**Problem**: `Address already in use`
- Solution: Change the port in `ui_server.py` from 5000 to another port

**Problem**: `ModuleNotFoundError: No module named 'flask'`
- Solution: Install Flask with `pip install flask`

### Traits not loading

**Problem**: "Loading traits..." stays displayed
- Solution: Check the browser console (F12) for JavaScript errors
- Make sure the Python server is running

### Drag & drop not working

**Problem**: Can't drag traits to the drop zone
- Solution: Ensure JavaScript is enabled in your browser
- Try refreshing the page

## Keyboard Shortcuts

- **Tab**: Navigate through form elements
- **Enter**: Submit (in text input fields)
- **Escape**: Close any dialogs

## Browser Compatibility

✅ Chrome/Chromium (recommended)
✅ Firefox
✅ Safari
✅ Edge

Requires modern browser with:
- Drag and drop API support
- CSS Grid support
- Fetch API support

## Tips & Tricks

1. **Experiment with combinations** - Try different trait combinations to see how they interact
2. **Use descriptive prompts** - Longer, more detailed prompts show better personality transformation
3. **Compare results** - Notice how different trait combinations create distinct personalities
4. **Create templates** - Remember your favorite combinations for reuse

## Performance

- **Lightweight**: Runs entirely on your local machine
- **Fast**: Responses generated instantly
- **No network required**: Works offline after initial load
- **Supports multiple agents**: Create and manage multiple personalities simultaneously

## Customization

To customize the UI:

### Change Colors
Edit `static/style.css` and modify the gradient colors:
```css
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
```

### Change Port
Edit `ui_server.py`:
```python
app.run(debug=True, host='localhost', port=8000)  # Change 5000 to your port
```

### Add New Traits
Add trait emojis in `ui_server.py`:
```python
emoji_map = {
    'YourTrait': '🎯',
}
```

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the main README.md
3. Run `python main.py` to test the core framework
4. Check browser console (F12) for errors

## Future Enhancements

- 💾 Save/load agent configurations
- 📊 Personality visualization charts
- 🎭 Preset personality templates
- 🔊 Text-to-speech output
- 🌐 Multi-user collaboration
- 📱 Mobile app version

## License

Part of the AI Agent Framework with Modular Personality System.

---

**Start creating unique personalities now!** 🚀
