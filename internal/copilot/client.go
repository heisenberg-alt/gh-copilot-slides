// Package copilot provides a client for the GitHub Copilot Chat
// Completions API. It handles OAuth device flow authentication and
// streaming chat responses for content generation and refinement.
package copilot

import (
	"bufio"
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"strings"
	"time"
)

const (
	// CopilotChatURL is the Copilot chat completions endpoint.
	CopilotChatURL = "https://api.githubcopilot.com/chat/completions"

	// GitHubDeviceCodeURL is the OAuth device authorization endpoint.
	GitHubDeviceCodeURL = "https://github.com/login/device/code"

	// GitHubTokenURL is the OAuth token exchange endpoint.
	GitHubTokenURL = "https://github.com/login/oauth/access_token"

	// DefaultClientID — users can override via GITHUB_COPILOT_CLIENT_ID
	DefaultClientID = "Iv1.b507a08c87ecfe98"

	// TokenEnvVar is the environment variable for a pre-existing token.
	TokenEnvVar = "GITHUB_TOKEN"
)

// Message represents a single chat message.
type Message struct {
	Role    string `json:"role"`    // "system", "user", "assistant"
	Content string `json:"content"`
}

// ChatRequest is the payload sent to the Copilot API.
type ChatRequest struct {
	Model    string    `json:"model"`
	Messages []Message `json:"messages"`
	Stream   bool      `json:"stream"`
}

// ChatChoice is a single completion choice.
type ChatChoice struct {
	Index   int     `json:"index"`
	Message Message `json:"message"`
	Delta   *struct {
		Content string `json:"content"`
	} `json:"delta,omitempty"`
}

// ChatResponse is the response from the Copilot API.
type ChatResponse struct {
	Choices []ChatChoice `json:"choices"`
}

// Client wraps the Copilot API with authentication.
type Client struct {
	Token      string
	HTTPClient *http.Client
	Model      string
}

// NewClient creates a Copilot client. It tries to use GITHUB_TOKEN
// from the environment, or falls back to a provided token.
func NewClient(token string) *Client {
	if envToken := os.Getenv(TokenEnvVar); envToken != "" {
		token = envToken
	}
	return &Client{
		Token:      token,
		HTTPClient: &http.Client{Timeout: 120 * time.Second},
		Model:      "gpt-4o",
	}
}

// Chat sends a non-streaming chat request and returns the full response text.
func (c *Client) Chat(messages []Message) (string, error) {
	req := ChatRequest{
		Model:    c.Model,
		Messages: messages,
		Stream:   false,
	}

	body, err := json.Marshal(req)
	if err != nil {
		return "", fmt.Errorf("marshaling request: %w", err)
	}

	httpReq, err := http.NewRequest("POST", CopilotChatURL, bytes.NewReader(body))
	if err != nil {
		return "", fmt.Errorf("creating request: %w", err)
	}
	c.setHeaders(httpReq)

	resp, err := c.HTTPClient.Do(httpReq)
	if err != nil {
		return "", fmt.Errorf("sending request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		respBody, _ := io.ReadAll(resp.Body)
		return "", fmt.Errorf("API error %d: %s", resp.StatusCode, string(respBody))
	}

	var chatResp ChatResponse
	if err := json.NewDecoder(resp.Body).Decode(&chatResp); err != nil {
		return "", fmt.Errorf("decoding response: %w", err)
	}

	if len(chatResp.Choices) == 0 {
		return "", fmt.Errorf("no choices in response")
	}
	return chatResp.Choices[0].Message.Content, nil
}

// StreamChat sends a streaming request and calls onChunk for each content delta.
func (c *Client) StreamChat(messages []Message, onChunk func(string)) error {
	req := ChatRequest{
		Model:    c.Model,
		Messages: messages,
		Stream:   true,
	}

	body, err := json.Marshal(req)
	if err != nil {
		return fmt.Errorf("marshaling request: %w", err)
	}

	httpReq, err := http.NewRequest("POST", CopilotChatURL, bytes.NewReader(body))
	if err != nil {
		return fmt.Errorf("creating request: %w", err)
	}
	c.setHeaders(httpReq)

	resp, err := c.HTTPClient.Do(httpReq)
	if err != nil {
		return fmt.Errorf("sending request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		respBody, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("API error %d: %s", resp.StatusCode, string(respBody))
	}

	scanner := bufio.NewScanner(resp.Body)
	for scanner.Scan() {
		line := scanner.Text()
		if !strings.HasPrefix(line, "data: ") {
			continue
		}
		data := strings.TrimPrefix(line, "data: ")
		if data == "[DONE]" {
			break
		}
		var chunk ChatResponse
		if err := json.Unmarshal([]byte(data), &chunk); err != nil {
			continue
		}
		if len(chunk.Choices) > 0 && chunk.Choices[0].Delta != nil {
			onChunk(chunk.Choices[0].Delta.Content)
		}
	}
	return scanner.Err()
}

func (c *Client) setHeaders(req *http.Request) {
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+c.Token)
	req.Header.Set("Editor-Version", "vscode/1.96.0")
	req.Header.Set("Copilot-Integration-Id", "slide-builder-ghcp")
}

// GenerateSlideContent asks Copilot to structure content into slide JSON.
func (c *Client) GenerateSlideContent(topic, purpose string, slideCount int, extraContext string) (string, error) {
	systemPrompt := `You are an expert presentation designer. Generate structured slide content as a JSON array.
Each slide object must have these fields:
- "type": one of "title", "content", "feature_grid", "code", "quote", "image", "closing"
- "title": the slide heading
- "subtitle": optional subtitle text
- "bullets": optional array of bullet points (max 6, each max 2 lines)
- "cards": optional array of {title, description, icon} for feature_grid (max 6)
- "code": optional code string for code slides
- "quote": optional quote text
- "attribution": optional quote attribution

Rules:
- First slide must be type "title"
- Last slide should be type "closing"
- Max 6 bullets per content slide
- Max 6 cards per feature_grid slide
- Keep text concise — each bullet should be 1-2 lines
- Return ONLY the JSON array, no markdown fences`

	userPrompt := fmt.Sprintf(
		"Create a %d-slide %s presentation about: %s\n\n%s",
		slideCount, purpose, topic, extraContext,
	)

	return c.Chat([]Message{
		{Role: "system", Content: systemPrompt},
		{Role: "user", Content: userPrompt},
	})
}

// SuggestStyle asks Copilot to recommend a style based on context.
func (c *Client) SuggestStyle(topic, purpose, mood string, availableStyles []string) (string, error) {
	systemPrompt := fmt.Sprintf(`You are a presentation design expert. Given the context, recommend the best style preset.
Available styles: %s

Return ONLY the style name (e.g., "neon_cyber"), nothing else.`, strings.Join(availableStyles, ", "))

	userPrompt := fmt.Sprintf(
		"Topic: %s\nPurpose: %s\nDesired feeling: %s\n\nWhich style preset best fits?",
		topic, purpose, mood,
	)

	return c.Chat([]Message{
		{Role: "system", Content: systemPrompt},
		{Role: "user", Content: userPrompt},
	})
}
