const express = require('express');
const app = express();
app.use(express.json());

app.post('/execute', (req, res) => {
    console.log(`[BANESCO] Ejecutando transferencia: ${req.body.amount} Bs.`);
    res.json({ tx_id: "BAN-" + Math.random().toString(36).substr(2, 9) });
});

app.listen(3000, () => console.log('Bank Bridge en 3000'));