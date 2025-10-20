# 🎨 Frontend Dockerfile - OpenGristAI
FROM node:18-alpine

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers de configuration
COPY package*.json ./
COPY svelte.config.js ./
COPY vite.config.ts ./
COPY tsconfig.json ./
COPY tailwind.config.ts ./
COPY postcss.config.js ./

# Installer les dépendances
RUN npm ci

# Copier le code source
COPY src ./src
COPY static ./static

# Exposer le port
EXPOSE 5173

# Commande de développement
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
