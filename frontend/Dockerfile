FROM node:22-slim

WORKDIR /app

COPY frontend/package.json frontend/package-lock.json ./
RUN npm config set registry https://registry.npmmirror.com \
  && npm ci

COPY frontend .

EXPOSE 3000

CMD ["sh", "-c", "printf '\\nQuantDash frontend is ready at: http://localhost:3000\\n\\n' && npm run dev -- --hostname 0.0.0.0"]
