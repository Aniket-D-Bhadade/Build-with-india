const express = require('express')
const path = require('path')
const app = express()
const port = 3000

// Serve static files from the current directory
app.use(express.static(path.join(__dirname)))

// Route for the home page
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'Home.html'))
})

// Route for the chatbot page
app.get('/chatbot', (req, res) => {
  res.sendFile(path.join(__dirname, 'chatbot.html'))
})

// Error handling for 404
app.use((req, res) => {
  res.status(404).send('Page not found')
})

// Error handling for other errors
app.use((err, req, res, next) => {
  console.error(err.stack)
  res.status(500).send('Something broke!')
})

app.listen(port, () => {
  console.log(`Server running at http://localhost:${port}`)
})