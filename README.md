# Bluesky Altometer

The Bluesky Altometer is a tool that measures the number of image posts on Bluesky that are missing alt text. It provides real-time statistics and a visual gauge to track the percentage of images lacking alternative text, promoting awareness about accessibility in the Bluesky social network.

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/Zetaphor/bluesky-altometer.git
   cd bluesky-altometer
   ```

2. Install the required Python packages:
   ```
   pip install -r requirements.txt
   ```

## Usage

1. Start the server:
   ```
   python main.py
   ```

2. Open a web browser and navigate to `http://localhost:8080`

3. The Bluesky Altometer will start tracking and displaying statistics about alt text usage in Bluesky image posts.

## How It Works

The Bluesky Altometer connects to the Bluesky Jetstream API to receive real-time updates about new posts. It analyzes each post containing images and checks for the presence of alt text. The data is stored in a SQLite database and served to the frontend via a WebSocket connection, allowing for live updates of the statistics and gauge.

## Written with Claude 3.5 Sonnet

I wrote the initial version of this tool with the assistance of Claude 3.5 Sonnet.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Powered by [Bluesky Jetstream](https://docs.bsky.app/blog/jetstream)
