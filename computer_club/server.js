const express = require('express');
const path = require('path');
const bodyParser = require('body-parser');
const axios = require('axios');

const app = express();
const PORT = process.env.PORT || 3000;

// Настройка body-parser
app.use(bodyParser.urlencoded({ extended: true }));
app.use(bodyParser.json());

// Настройка статических файлов
app.use(express.static(path.join(__dirname, 'pages')));
app.use('/styles', express.static(path.join(__dirname, 'styles')));
app.use('/tilda/css', express.static(path.join(__dirname, 'tilda', 'css')));
app.use('/tilda', express.static(path.join(__dirname, 'tilda')));
app.use('/src', express.static(path.join(__dirname, 'src')));

// Настройка маршрутов для рендеринга страниц
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'pages', 'login.html'));
});

app.get('/about', (req, res) => {
  res.sendFile(path.join(__dirname, 'tilda', 'page48758861.html'));
});

app.get('/profile', (req, res) => {
    res.sendFile(path.join(__dirname, 'pages', 'profile.html'));
});

app.get('/map', (req, res) => {
    res.sendFile(path.join(__dirname, 'pages', 'map.html'));
});

app.get('/register', (req, res) => {
    res.sendFile(path.join(__dirname, 'pages', 'register.html'));
});

app.get('/reservation', (req, res) => {
    res.sendFile(path.join(__dirname, 'pages', 'reservation.html'));
});

app.get('/promotions', (req, res) => {
    res.sendFile(path.join(__dirname, 'tilda', 'page48760289.html'));
});

app.post('/login', (req, res) => {
    const { email, password } = req.body;
  
    console.log(`Received email: ${email}`);
    console.log(`Received password: ${password}`);
  
    axios.post('http://localhost:5000/login', {
      email: email,
      password: password
    }, {
      headers: {
        'Content-Type': 'application/json'
      }
    })
    .then(response => {
      if (response.data.success) {
        res.redirect('/profile'); // Перенаправляем на страницу профиля
      } else {
        res.json(response.data);
      }
    })
    .catch(error => {
      res.status(500).json({ success: false, error: error.message });
    });
});

// Запуск сервера
app.listen(PORT, () => {
  console.log(`Server is running on http://localhost:${PORT}`);
});
