package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"strings"
	"time"

	"github.com/charmbracelet/bubbles/spinner"
	"github.com/charmbracelet/bubbles/textarea"
	"github.com/charmbracelet/bubbles/textinput"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

type field int

const (
	titleField field = iota
	descriptionField
	priorityField
	dueDateField
	submitButton
)

type responseMsg struct {
	success  bool
	response string
	err      error
}

type priority struct {
	name string
	icon string
}

var priorities = []priority{
	{name: "low", icon: "◆"},
	{name: "normal", icon: "●"},
	{name: "high", icon: "▲"},
	{name: "urgent", icon: "🚨"},
	{name: "message", icon: "💬"},
	{name: "info", icon: "ℹ"},
}

type model struct {
	width          int
	height         int
	focusIndex     field
	title          textinput.Model
	description    textarea.Model
	priorityIndex  int
	dueDate        textinput.Model
	spinner        spinner.Model
	loading        bool
	response       *responseMsg
	apiURL         string
}

func gradient(text string, startColor, endColor string) string {
	start := parseHexColor(startColor)
	end := parseHexColor(endColor)
	
	var result strings.Builder
	textLen := len(text)
	
	for i, char := range text {
		ratio := float64(i) / float64(textLen-1)
		if textLen == 1 {
			ratio = 0
		}
		
		r := int(float64(start[0]) + ratio*float64(end[0]-start[0]))
		g := int(float64(start[1]) + ratio*float64(end[1]-start[1]))
		b := int(float64(start[2]) + ratio*float64(end[2]-start[2]))
		
		color := lipgloss.Color(fmt.Sprintf("#%02x%02x%02x", r, g, b))
		result.WriteString(lipgloss.NewStyle().Foreground(color).Render(string(char)))
	}
	
	return result.String()
}

func parseHexColor(hex string) [3]int {
	hex = strings.TrimPrefix(hex, "#")
	var r, g, b int
	fmt.Sscanf(hex, "%02x%02x%02x", &r, &g, &b)
	return [3]int{r, g, b}
}

func initialModel() model {
	apiURL := os.Getenv("PRINTER_URL")
	if apiURL == "" {
		apiURL = "http://kiwi:33025"
	}

	ti := textinput.New()
	ti.Placeholder = "Enter task title"
	ti.Focus()
	ti.CharLimit = 156
	ti.Width = 70
	ti.PromptStyle = lipgloss.NewStyle().Foreground(lipgloss.Color("#FF6B9D"))
	ti.TextStyle = lipgloss.NewStyle().Foreground(lipgloss.Color("#FFFFFF"))
	ti.Cursor.Style = lipgloss.NewStyle().Foreground(lipgloss.Color("#FF6B9D"))

	ta := textarea.New()
	ta.Placeholder = "Describe your task (optional)"
	ta.CharLimit = 500
	ta.SetWidth(70)
	ta.SetHeight(6)
	ta.ShowLineNumbers = false
	ta.FocusedStyle.CursorLine = lipgloss.NewStyle()
	ta.FocusedStyle.Base = lipgloss.NewStyle().Foreground(lipgloss.Color("#FFFFFF"))
	ta.FocusedStyle.Placeholder = lipgloss.NewStyle().Foreground(lipgloss.Color("#666666"))
	ta.FocusedStyle.Prompt = lipgloss.NewStyle().Foreground(lipgloss.Color("#C7A2FF"))
	ta.BlurredStyle.Base = lipgloss.NewStyle().Foreground(lipgloss.Color("#888888"))
	ta.BlurredStyle.Placeholder = lipgloss.NewStyle().Foreground(lipgloss.Color("#444444"))
	ta.Cursor.Style = lipgloss.NewStyle().Foreground(lipgloss.Color("#C7A2FF"))
	ta.Prompt = ""

	di := textinput.New()
	di.Placeholder = "YYYY-MM-DD (optional)"
	di.CharLimit = 50
	di.Width = 70
	di.PromptStyle = lipgloss.NewStyle().Foreground(lipgloss.Color("#4DD9FF"))
	di.TextStyle = lipgloss.NewStyle().Foreground(lipgloss.Color("#FFFFFF"))
	di.Cursor.Style = lipgloss.NewStyle().Foreground(lipgloss.Color("#4DD9FF"))

	s := spinner.New()
	s.Spinner = spinner.Dot
	s.Style = lipgloss.NewStyle().Foreground(lipgloss.Color("#FF6B9D"))

	return model{
		focusIndex:    titleField,
		title:         ti,
		description:   ta,
		priorityIndex: 1,
		dueDate:       di,
		spinner:       s,
		apiURL:        apiURL,
	}
}

func (m model) Init() tea.Cmd {
	return tea.Batch(textinput.Blink, m.spinner.Tick)
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	var cmd tea.Cmd
	var cmds []tea.Cmd

	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		m.width = msg.Width
		m.height = msg.Height
		return m, nil

	case tea.KeyMsg:
		if m.loading {
			return m, nil
		}

		if m.response != nil {
			return m, tea.Quit
		}

		switch msg.String() {
		case "ctrl+c", "q":
			return m, tea.Quit

		case "left", "right":
			if m.focusIndex == priorityField {
				if msg.String() == "left" {
					m.priorityIndex--
					if m.priorityIndex < 0 {
						m.priorityIndex = len(priorities) - 1
					}
				} else {
					m.priorityIndex++
					if m.priorityIndex >= len(priorities) {
						m.priorityIndex = 0
					}
				}
				return m, nil
			}

		case "tab", "shift+tab", "up", "down":
			s := msg.String()

			if s == "up" || s == "shift+tab" {
				m.focusIndex--
			} else {
				m.focusIndex++
			}

			if m.focusIndex > submitButton {
				m.focusIndex = titleField
			} else if m.focusIndex < titleField {
				m.focusIndex = submitButton
			}

			for i := titleField; i <= dueDateField; i++ {
				if i == m.focusIndex {
					switch i {
					case titleField:
						cmds = append(cmds, m.title.Focus())
					case descriptionField:
						cmds = append(cmds, m.description.Focus())
					case dueDateField:
						cmds = append(cmds, m.dueDate.Focus())
					}
				} else {
					switch i {
					case titleField:
						m.title.Blur()
					case descriptionField:
						m.description.Blur()
					case dueDateField:
						m.dueDate.Blur()
					}
				}
			}

			return m, tea.Batch(cmds...)

		case "enter":
			if m.focusIndex == submitButton {
				m.loading = true
				return m, tea.Batch(m.spinner.Tick, m.submitTask())
			}
			if m.focusIndex == descriptionField {
				m.description, cmd = m.description.Update(msg)
				return m, cmd
			}
		}

	case responseMsg:
		m.loading = false
		m.response = &msg
		
		// Show response for 1 second then quit
		return m, tea.Tick(1*time.Second, func(t time.Time) tea.Msg {
			return tea.Quit()
		})

	case spinner.TickMsg:
		if m.loading {
			m.spinner, cmd = m.spinner.Update(msg)
			return m, cmd
		}
	}

	if !m.loading && m.response == nil {
		switch m.focusIndex {
		case titleField:
			m.title, cmd = m.title.Update(msg)
		case descriptionField:
			m.description, cmd = m.description.Update(msg)
		case dueDateField:
			m.dueDate, cmd = m.dueDate.Update(msg)
		}
	}

	return m, cmd
}

func (m model) View() string {
	if m.width == 0 {
		return ""
	}

	if m.response != nil {
		return m.renderResponse()
	}

	if m.loading {
		return m.renderLoading()
	}

	return m.renderForm()
}

func (m model) renderForm() string {
	var content strings.Builder

	titleText := "THERMAL PRINTER"
	headerGradient := gradient(titleText, "#FF6B9D", "#C7A2FF")
	
	headerStyle := lipgloss.NewStyle().
		Padding(1, 0).
		Width(m.width).
		Align(lipgloss.Center).
		Bold(true)

	header := headerStyle.Render(headerGradient)
	content.WriteString(header + "\n")

	formWidth := 76
	formStyle := lipgloss.NewStyle().
		Width(formWidth).
		Align(lipgloss.Left)

	var formContent strings.Builder

	labelStyle := func(color string, active bool) lipgloss.Style {
		s := lipgloss.NewStyle().Foreground(lipgloss.Color(color)).Bold(true)
		if active {
			return s
		}
		return lipgloss.NewStyle().Foreground(lipgloss.Color("#666666")).Bold(true)
	}

	active := m.focusIndex == titleField
	label := labelStyle("#FF6B9D", active).Render("TITLE")
	if active {
		label = "▶ " + label
	} else {
		label = "  " + label
	}
	formContent.WriteString(label + "\n")
	formContent.WriteString("  " + m.title.View() + "\n\n")

	active = m.focusIndex == descriptionField
	label = labelStyle("#C7A2FF", active).Render("DESCRIPTION")
	if active {
		label = "▶ " + label
	} else {
		label = "  " + label
	}
	formContent.WriteString(label + "\n")
	formContent.WriteString("  " + m.description.View() + "\n\n")

	active = m.focusIndex == priorityField
	label = labelStyle("#FFD93D", active).Render("PRIORITY")
	if active {
		label = "▶ " + label
	} else {
		label = "  " + label
	}
	formContent.WriteString(label + "\n")

	var priorityButtons strings.Builder
	for i, p := range priorities {
		var btnStyle lipgloss.Style
		if i == m.priorityIndex {
			if active {
				btnStyle = lipgloss.NewStyle().
					Foreground(lipgloss.Color("#000000")).
					Background(lipgloss.Color("#FFD93D")).
					Padding(0, 2).
					Bold(true)
			} else {
				btnStyle = lipgloss.NewStyle().
					Foreground(lipgloss.Color("#FFD93D")).
					Background(lipgloss.Color("#333333")).
					Padding(0, 2)
			}
		} else {
			btnStyle = lipgloss.NewStyle().
				Foreground(lipgloss.Color("#666666")).
				Background(lipgloss.Color("#1a1a1a")).
				Padding(0, 2)
		}
		priorityButtons.WriteString(btnStyle.Render(p.icon + " " + p.name))
		if i < len(priorities)-1 {
			priorityButtons.WriteString(" ")
		}
	}
	formContent.WriteString("  " + priorityButtons.String() + "\n\n")

	active = m.focusIndex == dueDateField
	label = labelStyle("#4DD9FF", active).Render("DUE DATE")
	if active {
		label = "▶ " + label
	} else {
		label = "  " + label
	}
	formContent.WriteString(label + "\n")
	formContent.WriteString("  " + m.dueDate.View() + "\n\n")

	var submitBtn lipgloss.Style
	if m.focusIndex == submitButton {
		submitBtn = lipgloss.NewStyle().
			Foreground(lipgloss.Color("#000000")).
			Background(lipgloss.Color("#00FF88")).
			Padding(0, 3).
			Bold(true)
	} else {
		submitBtn = lipgloss.NewStyle().
			Foreground(lipgloss.Color("#666666")).
			Background(lipgloss.Color("#1a1a1a")).
			Padding(0, 3)
	}
	
	formContent.WriteString("  " + submitBtn.Render("SEND TO PRINTER") + "\n")

	form := formStyle.Render(formContent.String())
	content.WriteString(lipgloss.Place(m.width, m.height-6, lipgloss.Center, lipgloss.Top, form))

	helpStyle := lipgloss.NewStyle().
		Foreground(lipgloss.Color("#666666")).
		Width(m.width).
		Align(lipgloss.Center)

	help := helpStyle.Render("tab: next • ←/→: change priority • enter: submit • q: quit")
	content.WriteString("\n" + help)

	return content.String()
}

func (m model) renderLoading() string {
	loadingText := fmt.Sprintf("%s  Sending to printer", m.spinner.View())
	
	loadingStyle := lipgloss.NewStyle().
		Foreground(lipgloss.Color("#FF6B9D")).
		Bold(true).
		Width(m.width).
		Height(m.height).
		Align(lipgloss.Center, lipgloss.Center)

	return loadingStyle.Render(loadingText)
}

func (m model) renderResponse() string {
	var content strings.Builder

	if m.response.success {
		successText := gradient("SUCCESS", "#00FF88", "#4DD9FF")
		
		headerStyle := lipgloss.NewStyle().
			Padding(1, 0).
			Width(m.width).
			Align(lipgloss.Center).
			Bold(true)

		header := headerStyle.Render("✓ " + successText + " ✓")
		content.WriteString(header + "\n\n")

		responseBox := lipgloss.NewStyle().
			Border(lipgloss.RoundedBorder()).
			BorderForeground(lipgloss.Color("#00FF88")).
			Padding(1, 2).
			Width(70).
			Foreground(lipgloss.Color("#FFFFFF"))

		jsonFormatted := m.response.response
		responseContent := responseBox.Render(jsonFormatted)
		content.WriteString(lipgloss.Place(m.width, m.height-4, lipgloss.Center, lipgloss.Center, responseContent))

	} else {
		errorText := gradient("ERROR", "#FF0000", "#FF6B9D")
		
		headerStyle := lipgloss.NewStyle().
			Padding(1, 0).
			Width(m.width).
			Align(lipgloss.Center).
			Bold(true)

		header := headerStyle.Render("✗ " + errorText + " ✗")
		content.WriteString(header + "\n\n")

		errorBox := lipgloss.NewStyle().
			Border(lipgloss.RoundedBorder()).
			BorderForeground(lipgloss.Color("#FF0000")).
			Padding(1, 2).
			Width(70).
			Foreground(lipgloss.Color("#FF6B9D"))

		errorContent := errorBox.Render(fmt.Sprintf("Error: %v\n\n%s", m.response.err, m.response.response))
		content.WriteString(lipgloss.Place(m.width, m.height-4, lipgloss.Center, lipgloss.Center, errorContent))
	}

	helpStyle := lipgloss.NewStyle().
		Foreground(lipgloss.Color("#666666")).
		Width(m.width).
		Align(lipgloss.Center)

	help := helpStyle.Render("closing in 1 second...")
	content.WriteString("\n" + help)

	return content.String()
}

func (m model) submitTask() tea.Cmd {
	return func() tea.Msg {
		title := strings.TrimSpace(m.title.Value())
		if title == "" {
			return responseMsg{
				success:  false,
				err:      fmt.Errorf("title is required"),
				response: "",
			}
		}

		selectedPriority := priorities[m.priorityIndex]

		payload := map[string]interface{}{
			"title":       title,
			"description": m.description.Value(),
			"priority":    selectedPriority.name,
		}

		dueDate := strings.TrimSpace(m.dueDate.Value())
		if dueDate != "" {
			payload["due_date"] = dueDate
		}

		jsonData, err := json.Marshal(payload)
		if err != nil {
			return responseMsg{
				success:  false,
				err:      err,
				response: "",
			}
		}

		time.Sleep(500 * time.Millisecond)

		resp, err := http.Post(m.apiURL+"/print-task", "application/json", bytes.NewBuffer(jsonData))
		if err != nil {
			return responseMsg{
				success:  false,
				err:      err,
				response: "",
			}
		}
		defer resp.Body.Close()

		body, _ := io.ReadAll(resp.Body)

		var prettyJSON bytes.Buffer
		json.Indent(&prettyJSON, body, "", "  ")

		if resp.StatusCode != http.StatusOK {
			return responseMsg{
				success:  false,
				err:      fmt.Errorf("server returned status %d", resp.StatusCode),
				response: prettyJSON.String(),
			}
		}

		return responseMsg{
			success:  true,
			response: prettyJSON.String(),
			err:      nil,
		}
	}
}

func main() {
	m := initialModel()
	p := tea.NewProgram(
		m,
		tea.WithAltScreen(),
		tea.WithMouseCellMotion(),
	)
	finalModel, err := p.Run()
	if err != nil {
		fmt.Printf("Error: %v\n", err)
		os.Exit(1)
	}
	
	// After TUI exits, print response to stdout
	if fm, ok := finalModel.(model); ok && fm.response != nil {
		if fm.response.success {
			fmt.Println("\n✓ Task sent successfully!")
			fmt.Println(fm.response.response)
		} else {
			fmt.Printf("\n✗ Error: %v\n", fm.response.err)
			if fm.response.response != "" {
				fmt.Println(fm.response.response)
			}
		}
	}
}
