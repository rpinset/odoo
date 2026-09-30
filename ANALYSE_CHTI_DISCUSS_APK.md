# Analyse de l'application Android Ch'ti Discuss (Odoo)

## Résumé

**Ch'ti Discuss** est une application mobile React Native/Expo qui fonctionne comme client du module **Odoo Discuss**, offrant une expérience type Discord (messagerie en temps réel, canaux, messages directs, réactions, partage de fichiers).

---

## 1. Identification de l'application

| Propriété | Valeur |
|-----------|--------|
| **Nom** | Ch'ti Discuss |
| **Package Android** | `fr.chtitech.discuss` |
| **Version** | 0.1.0 |
| **SDK Expo** | 55.0.0 |
| **Éditeur** | Ch'ti Tech (https://www.chti-tech.eu/) |
| **Description** | Client Odoo Discuss style Discord — Desktop & Mobile |

---

## 2. Stack technique

- **Framework** : React Native + Expo (SDK 55)
- **Build** : EAS (Expo Application Services) - Project ID: `05bad5ce-9337-4e1f-ad65-e9e37c1e45b1`
- **Navigation** : React Navigation (Drawer, Stack)
- **Animations** : React Native Reanimated
- **Notifications** : expo-notifications, Firebase Cloud Messaging
- **Mise à jour OTA** : expo-updates (https://u.expo.dev/05bad5ce-9337-4e1f-ad65-e9e37c1e45b1)

---

## 3. Intégration Odoo

### 3.1 Modèles Odoo utilisés

| Modèle | Usage |
|--------|-------|
| `mail.channel` | Canaux de discussion (équivalent Discuss) |
| `discuss.channel` | Canaux avec séparateurs de messages |
| `res.partner` | Partenaires/utilisateurs (liens `data-oe-model`, `data-oe-id`) |

### 3.2 Authentification

- **API key** : Support des clés API Odoo (Préférences > API Keys)
- **2FA** : Obligatoire si 2FA activé sur le compte
- **Session** : Stockage via `chti_discuss_sessionId` (AsyncStorage)
- **Champs login** : `login.instance_ur`, `login.apikey_placeholder`

Message d'erreur : *"Invalid API key. Generate one in Odoo > Preferences > API Keys. Required if 2FA is enabled."*

### 3.3 Communication temps réel

- **BusService** : Service WebSocket pour la messagerie temps réel
  - Polling ORM en mode API key
  - Reconnexion automatique en cas de fermeture WebSocket
  - Gestion des erreurs : parse, connexion, notifications non gérées

### 3.4 Fonctionnalités Discuss

- **Messages** : Envoi, édition, suppression
- **Canaux** : Liste, sélection, création, quitter
- **Threads** : Réponses dans les fils de discussion
- **Réactions** : Système de réactions aux messages
- **Fichiers** : Pièces jointes, images, documents
- **Prévisualisation** : `mail.link.preview` pour les liens
- **Mute** : `header.mute_until_dt` pour les canaux silencieux
- **Notifications** : Push notifications

---

## 4. Structure des composants

| Composant | Rôle |
|-----------|------|
| **BusService** | WebSocket, polling ORM, gestion des notifications |
| **ChannelList** | Liste des canaux, état pin/hide |
| **ChatScreen** | Écran de chat, envoi, threads, mute, recherche |
| **Composer** | Saisie de messages, DocumentPicker, ImagePicker |
| **ChannelSelector** | Sélection de canaux |

---

## 5. Messages d'erreur identifiés

```
[BusService] ORM poll error
[BusService] Peek poll error
[BusService] Unhandled notification
[BusService] WS parse error
[BusService] WebSocket closed, reconnecting...
[BusService] WebSocket error
[Bus] Failed to fetch attachments
[Bus] Failed to start
[ChannelList] Failed to load pin/hide state
[ChatScreen] Failed to send thread reply
[ChatScreen] Leave failed
[ChatScreen] Mute toggle failed
[ChatScreen] Search failed
[Composer] DocumentPicker not available
[Composer] ImagePicker not available
[OdooContext] Edit message failed
```

---

## 6. Permissions Android

- `INTERNET` : Communication avec Odoo
- `CAMERA` : Prise de photos
- `READ_EXTERNAL_STORAGE` / `READ_MEDIA_IMAGES` / `READ_MEDIA_VIDEO` : Accès aux médias
- `RECORD_AUDIO` : Enregistrement audio

---

## 7. Architecture technique

```
┌─────────────────────────────────────────────────────────────┐
│                    Ch'ti Discuss (Expo)                      │
├─────────────────────────────────────────────────────────────┤
│  React Navigation  │  React Native Reanimated  │  Expo       │
├─────────────────────────────────────────────────────────────┤
│  BusService (WebSocket)  │  Odoo API (JSON-RPC/XML-RPC)       │
├─────────────────────────────────────────────────────────────┤
│                    Odoo Backend (Discuss)                     │
│  mail.channel │ discuss.channel │ res.partner │ Bus         │
└─────────────────────────────────────────────────────────────┘
```

---

## 8. Fichiers clés extraits

| Fichier | Contenu |
|---------|---------|
| `assets/app.config` | Configuration Expo (nom, slug, version, permissions) |
| `assets/index.android.bundle` | Bundle JS compilé (Hermes bytecode) |
| `assets/app.manifest` | Manifest des assets |

---

## 9. Recommandations pour l'intégration

1. **Authentification** : Configurer les clés API dans Odoo (Préférences > API Keys) si 2FA est activé
2. **Backend** : Instance Odoo avec module Discuss activé
3. **WebSocket** : URL du bus Odoo accessible depuis le réseau mobile
4. **CORS** : Autoriser les requêtes depuis l'app si nécessaire

---

## 10. Références

- [Odoo Discuss Documentation](https://www.odoo.com/documentation/master/applications/productivity/discuss.html)
- [Ch'ti Tech](https://www.chti-tech.eu/)
- [Expo SDK 55](https://docs.expo.dev/)
