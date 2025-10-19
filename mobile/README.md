# FALA Mobile

Aplicativo React Native (Expo) para artistas gerenciarem músicas, transcrições e edições automáticas.

## Como rodar em desenvolvimento

```bash
cd mobile
npm install            # ou yarn / pnpm
npm run start          # inicia Metro bundler (Expo)
```

Use `npm run ios` / `npm run android` para builds nativas via Expo.

## Estrutura

- `App.tsx`: bootstrap do React Navigation com tema personalizado.
- `src/theme`: tokens de cores, espaçamento e tipografia seguindo a identidade dourada/preto.
- `src/components`: botões, cards, chips e timeline prontos para reutilização.
- `src/screens`: telas Home, Biblioteca, Upload, Transcrições, Novo Reels, Edições, Resultado e Configurações (todas baseadas em guidelines Apple/Google).
- `src/navigation`: configuração do stack + bottom tabs.

## Próximos passos

1. Adicionar fluxo de autenticação (login/signup) e integração com backend.
2. Implementar stores (Zustand/React Query) para consumir API real.
3. Conectar componentes de upload com Expo FileSystem/DocumentPicker.
4. Suportar notificações push (Expo Notifications) e deep links.
5. Ajustar assets reais (`assets/icon.png`, `splash.png`, etc.) antes de enviar às lojas.
