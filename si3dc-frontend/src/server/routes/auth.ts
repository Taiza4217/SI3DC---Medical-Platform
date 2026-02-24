import { Router } from 'express';
import { users } from '../db';

export const authRouter = Router();

authRouter.post('/login', (req, res) => {
  const { professionalId, password, healthNetwork } = req.body;

  if (!professionalId || !password || !healthNetwork) {
    return res.status(400).json({ message: 'Todos os campos são obrigatórios.' });
  }

  // Find the user in our mock DB
  const user = users.find(
    (u) =>
      u.professionalId.toLowerCase() === professionalId.toLowerCase() &&
      u.healthNetworkId === healthNetwork
  );

  // Check if user exists and password is correct
  if (!user || user.password !== password) {
    return res.status(401).json({ message: 'Credenciais inválidas para esta rede de saúde.' });
  }

  // On success, return a success message and user info (without password)
  // In a real app, you would return a JWT (JSON Web Token) here.
  res.status(200).json({
    message: 'Login bem-sucedido!',
    user: {
      name: user.name,
      professionalId: user.professionalId,
      permissionLevel: user.permissionLevel, // This is for internal use, not shown to the user
    },
  });
});
