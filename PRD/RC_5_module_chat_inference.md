# RC_5 — Module Chat : API Conversationnelle & Frontend Type ChatGPT

## 1. Objectifs

Module **`chat`** : Interface conversationnelle complète type ChatGPT avec :
- **API REST** : `/api/chat/completions` (compatible OpenAI)
- **WebSocket** : `/ws/chat` pour streaming token-par-token
- **Frontend React** : ChatInterface, MessageBubble, TokenStream, ModelSelector
- **Historique** : Sessions persistées, branches, export

---

## 2. Structure Module `chat`

```
apps/modules/chat/
├── __init__.py
├── models/
│   ├── __init__.py
│   └── chatModel.py             # ChatSession, ChatMessage, GenerationOptions, ChatCompletionRequest/Response
├── repositories/
│   ├── __init__.py
│   └── chatRepository.py        # Sessions, messages, branches
├── services/
│   ├── __init__.py
│   └── chatService.py           # Orchestration chat + appel InferenceService
├── controllers/
│   ├── __init__.py
│   ├── chatController.py        # REST /api/chat
│   └── wsChatController.py      # WebSocket /ws/chat
└── frontend/                    # Code React (dans web/src/features/chat)
    ├── components/
    │   ├── ChatInterface.tsx
    │   ├── MessageBubble.tsx
    │   ├── TokenStream.tsx
    │   ├── ModelSelector.tsx
    │   ├── SessionSidebar.tsx
    │   └── SystemPromptEditor.tsx
    ├── hooks/
    │   ├── useChatSession.ts
    │   ├── useWebSocket.ts
    │   └── useTokenStream.ts
    ├── api/
    │   └── chatApi.ts
    └── index.ts
```

---

## 3. Modèles de Domaine (`chatModel.py`)

```python
# apps/modules/chat/models/chatModel.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal
from uuid import uuid4

@dataclass(frozen=True)
class ChatMessage:
    id: str = field(default_factory=lambda: str(uuid4()))
    role: Literal["system", "user", "assistant"]
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    tokens: int | None = None
    generationOptions: GenerationOptions | None = None
    checkpointId: str | None = None
    parentId: str | None = None      # Pour branchement conversation
    metadata: dict = field(default_factory=dict)

@dataclass(frozen=True)
class ChatSession:
    id: str = field(default_factory=lambda: str(uuid4()))
    userId: str
    title: str
    systemPrompt: str = "Tu es un assistant IA utile et inoffensif."
    messages: list[ChatMessage] = field(default_factory=list)
    currentBranch: str = "main"
    branches: dict[str, list[ChatMessage]] = field(default_factory=lambda: {"main": []})
    createdAt: datetime = field(default_factory=datetime.utcnow)
    updatedAt: datetime = field(default_factory=datetime.utcnow)
    metadata: dict = field(default_factory=dict)
    
    def addMessage(self, message: ChatMessage, branch: str | None = None) -> "ChatSession":
        branch = branch or self.currentBranch
        newBranches = {**self.branches}
        newBranches[branch] = [*newBranches.get(branch, []), message]
        return ChatSession(
            **{**self.__dict__, "messages": newBranches[branch], "branches": newBranches, "updatedAt": datetime.utcnow()}
        )
    
    def getContext(self, branch: str | None = None, maxTokens: int = 4096) -> list[ChatMessage]:
        branch = branch or self.currentBranch
        msgs = self.branches.get(branch, [])
        # Tronque pour respecter maxTokens (estimation)
        return msgs[-20:]  # Simplifié

@dataclass(frozen=True)
class GenerationOptions:
    maxTokens: int = 512
    temperature: float = 0.7
    topK: int | None = 50
    topP: float = 0.9
    repetitionPenalty: float = 1.1
    stopSequences: list[str] = field(default_factory=list)
    seed: int | None = None
    stream: bool = True

# OpenAI-compatible
@dataclass(frozen=True)
class ChatCompletionRequest:
    model: str                      # checkpoint ID ou "latest"
    messages: list[dict]            # [{"role": "user", "content": "..."}]
    temperature: float = 0.7
    top_p: float = 1.0
    max_tokens: int | None = 512
    stream: bool = False
    stop: list[str] | None = None
    user: str | None = None

@dataclass(frozen=True)
class ChatCompletionResponse:
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: list[dict]
    usage: dict

@dataclass(frozen=True)
class ChatCompletionChunk:
    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str
    choices: list[dict]             # delta avec content
```

---

## 4. Repository (`chatRepository.py`)

```python
# apps/modules/chat/repositories/chatRepository.py
class ChatRepository:
    def __init__(self, baseDir: Path):
        self._baseDir = baseDir
        self._sessionsDb = baseDir / "chat_sessions.sqlite"
        self._initDb()
    
    def saveSession(self, session: ChatSession) -> ChatSession:
        # Upsert session + messages
        ...
    
    def findSessionById(self, sessionId: str) -> ChatSession | None:
        ...
    
    def findSessionsByUser(self, userId: str, limit: int = 50, offset: int = 0) -> list[ChatSession]:
        ...
    
    def deleteSession(self, sessionId: str, userId: str) -> bool:
        ...
    
    def forkSession(self, sessionId: str, forkPointMessageId: str, newTitle: str, userId: str) -> ChatSession:
        # Crée nouvelle session à partir d'un message existant
        ...
    
    def exportSession(self, sessionId: str, format: Literal["json", "markdown", "txt"]) -> str:
        ...
```

---

## 5. Service (`chatService.py`)

```python
# apps/modules/chat/services/chatService.py
class ChatService:
    def __init__(
        self,
        chatRepo: ChatRepository,
        inferenceService: InferenceService,  # Dépendance cross-module
        tokenizerRepo: TokenizerRepository,
        jobRepo: JobRepository,
    ):
        ...
    
    def createSession(self, userId: str, title: str | None = None, systemPrompt: str | None = None) -> ChatSession:
        session = ChatSession(
            userId=userId,
            title=title or f"Conversation {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
            systemPrompt=systemPrompt or "Tu es un assistant IA utile et inoffensif."
        )
        self._chatRepo.saveSession(session)
        return session
    
    def sendMessage(
        self,
        sessionId: str,
        userId: str,
        content: str,
        options: GenerationOptions | None = None,
        branch: str | None = None,
        checkpointId: str | None = None,
    ) -> ChatMessage:
        session = self._chatRepo.findSessionById(sessionId)
        if not session or session.userId != userId:
            raise ResourceNotFoundError("Session")
        
        userMsg = ChatMessage(role="user", content=content)
        session = session.addMessage(userMsg, branch)
        
        # Appel inférence
        context = session.getContext(branch)
        prompt = self._buildPrompt(session.systemPrompt, context)
        
        if options and options.stream:
            # Pour streaming, retourne un générateur
            return self._streamResponse(session, branch, prompt, options, checkpointId)
        else:
            response = self._inferenceService.generate(prompt, options or GenerationOptions(), checkpointId)
            assistantMsg = ChatMessage(
                role="assistant",
                content=response,
                generationOptions=options,
                checkpointId=checkpointId
            )
            session = session.addMessage(assistantMsg, branch)
            self._chatRepo.saveSession(session)
            return assistantMsg
    
    def _buildPrompt(self, systemPrompt: str, messages: list[ChatMessage]) -> str:
        parts = [f"<|system|>\n{systemPrompt}"]
        for msg in messages:
            role = msg.role
            parts.append(f"<|{role}|>\n{msg.content}")
        parts.append("<|assistant|>\n")
        return "\n".join(parts)
    
    def _streamResponse(self, session: ChatSession, branch: str, prompt: str, 
                        options: GenerationOptions, checkpointId: str) -> Iterator[str]:
        fullResponse = ""
        for token in self._inferenceService.streamGenerate(prompt, options, checkpointId):
            fullResponse += token
            yield token
        
        assistantMsg = ChatMessage(
            role="assistant",
            content=fullResponse,
            generationOptions=options,
            checkpointId=checkpointId
        )
        session = session.addMessage(assistantMsg, branch)
        self._chatRepo.saveSession(session)
    
    def forkConversation(self, sessionId: str, messageId: str, userId: str, title: str) -> ChatSession:
        return self._chatRepo.forkSession(sessionId, messageId, title, userId)
    
    def renameSession(self, sessionId: str, userId: str, newTitle: str) -> ChatSession:
        session = self._chatRepo.findSessionById(sessionId)
        if not session or session.userId != userId:
            raise ResourceNotFoundError("Session")
        updated = ChatSession(**{**session.__dict__, "title": newTitle})
        self._chatRepo.saveSession(updated)
        return updated
```

---

## 6. Controllers

### `chatController.py` — REST API (OpenAI-compatible)

```python
# apps/modules/chat/controllers/chatController.py
chatBlueprint = Blueprint("chat", __name__, url_prefix="/api/chat")

@chatBlueprint.route("/completions", methods=["POST"])
@requireAuth
@validateInput(ChatCompletionRequest)
def createCompletion(validated: ChatCompletionRequest, user: User):
    options = GenerationOptions(
        maxTokens=validated.max_tokens,
        temperature=validated.temperature,
        topP=validated.top_p,
        stopSequences=validated.stop or [],
        stream=validated.stream
    )
    
    if validated.stream:
        return Response(
            _streamOpenAIResponse(validated, options, user),
            mimetype="text/event-stream"
        )
    
    # Non-streaming
    session = chatService.createSession(user.id)
    # Convert messages to prompt
    prompt = _messagesToPrompt(validated.messages)
    response = chatService._inferenceService.generate(prompt, options, validated.model)
    
    return jsonify(ChatCompletionResponse(
        id=str(uuid4()),
        created=int(time.time()),
        model=validated.model,
        choices=[{"index": 0, "message": {"role": "assistant", "content": response}, "finish_reason": "stop"}],
        usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    ))

def _streamOpenAIResponse(req: ChatCompletionRequest, options: GenerationOptions, user: User):
    prompt = _messagesToPrompt(req.messages)
    for token in chatService._inferenceService.streamGenerate(prompt, options, req.model):
        chunk = ChatCompletionChunk(
            id=str(uuid4()),
            created=int(time.time()),
            model=req.model,
            choices=[{"index": 0, "delta": {"content": token}, "finish_reason": None}]
        )
        yield f"data: {chunk.to_json()}\n\n"
    yield "data: [DONE]\n\n"

@chatBlueprint.route("/sessions", methods=["GET"])
@requireAuth
def listSessions(user: User):
    sessions = chatRepo.findSessionsByUser(user.id)
    return jsonify([ChatSessionSummary.fromSession(s) for s in sessions])

@chatBlueprint.route("/sessions", methods=["POST"])
@requireAuth @validateInput(CreateSessionRequest)
def createSession(validated: CreateSessionRequest, user: User):
    session = chatService.createSession(user.id, validated.title, validated.systemPrompt)
    return jsonify(ChatSessionResponse.fromSession(session)), 201

@chatBlueprint.route("/sessions/<sessionId>", methods=["GET"])
@requireAuth
def getSession(sessionId: str, user: User):
    session = chatRepo.findSessionById(sessionId)
    if not session or session.userId != user.id:
        raise ResourceNotFoundError("Session")
    return jsonify(ChatSessionResponse.fromSession(session))

@chatBlueprint.route("/sessions/<sessionId>", methods=["DELETE"])
@requireAuth
def deleteSession(sessionId: str, user: User):
    chatRepo.deleteSession(sessionId, user.id)
    return "", 204

@chatBlueprint.route("/sessions/<sessionId>/fork", methods=["POST"])
@requireAuth @validateInput(ForkSessionRequest)
def forkSession(sessionId: str, validated: ForkSessionRequest, user: User):
    session = chatService.forkConversation(sessionId, validated.messageId, user.id, validated.title)
    return jsonify(ChatSessionResponse.fromSession(session)), 201

@chatBlueprint.route("/sessions/<sessionId>/export", methods=["GET"])
@requireAuth
def exportSession(sessionId: str, user: User, format: str = "json"):
    content = chatRepo.exportSession(sessionId, format)
    return Response(content, mimetype={"json": "application/json", "markdown": "text/markdown", "txt": "text/plain"}[format])
```

### `wsChatController.py` — WebSocket Streaming

```python
# apps/modules/chat/controllers/wsChatController.py
from flask_sock import Sock

sock = Sock()

@sock.route("/ws/chat")
def wsChat(ws, user: User):
    """WebSocket pour streaming temps réel token par token."""
    try:
        while True:
            data = ws.receive()
            if not data:
                break
            
            msg = json.loads(data)
            if msg["type"] == "chat":
                sessionId = msg.get("sessionId")
                content = msg["content"]
                options = GenerationOptions(**msg.get("options", {}))
                checkpointId = msg.get("checkpointId")
                
                session = chatRepo.findSessionById(sessionId) if sessionId else chatService.createSession(user.id)
                
                userMsg = ChatMessage(role="user", content=content)
                session = session.addMessage(userMsg)
                
                prompt = chatService._buildPrompt(session.systemPrompt, session.getContext())
                
                # Stream tokens
                ws.send(json.dumps({"type": "start", "messageId": userMsg.id}))
                
                fullResponse = ""
                for token in chatService._inferenceService.streamGenerate(prompt, options, checkpointId):
                    fullResponse += token
                    ws.send(json.dumps({"type": "token", "content": token}))
                
                assistantMsg = ChatMessage(role="assistant", content=fullResponse, generationOptions=options, checkpointId=checkpointId)
                session = session.addMessage(assistantMsg)
                chatRepo.saveSession(session)
                
                ws.send(json.dumps({"type": "end", "messageId": assistantMsg.id, "usage": {...}}))
            
            elif msg["type"] == "ping":
                ws.send(json.dumps({"type": "pong"}))
    
    except Exception as e:
        ws.send(json.dumps({"type": "error", "message": str(e)}))
    finally:
        ws.close()
```

---

## 7. Frontend React (Architecture)

### Structure `web/src/features/chat/`

```
web/src/features/chat/
├── index.ts                     # Exports publics
├── api/
│   └── chatApi.ts               # Appels REST + WebSocket client
├── hooks/
│   ├── useChatSession.ts        # État session courante
│   ├── useWebSocket.ts          # Connexion WS, reconnexion auto
│   └── useTokenStream.ts        # Buffer tokens, rendering progressif
├── components/
│   ├── ChatInterface.tsx        # Container principal
│   ├── MessageBubble.tsx        # Bulle message (user/assistant/system)
│   ├── TokenStream.tsx          # Affichage streaming avec curseur
│   ├── ModelSelector.tsx        # Dropdown sélection checkpoint
│   ├── SessionSidebar.tsx       # Liste sessions, nouvelle, fork, supprimer
│   ├── SystemPromptEditor.tsx   # Modal éditeur system prompt
│   └── ChatInput.tsx            # Zone saisie + envoi
├── types/
│   └── chat.ts                  # Types TypeScript (alignés Python)
└── utils/
    └── markdown.ts              # Rendering markdown (code blocks, etc.)
```

### `ChatInterface.tsx` — Composant Principal

```tsx
// web/src/features/chat/components/ChatInterface.tsx
import { Box, Flex, Stack, Text, Heading, Button, Input, Select } from '@/components/atoms';
import { MessageBubble } from './MessageBubble';
import { TokenStream } from './TokenStream';
import { SessionSidebar } from './SessionSidebar';
import { ModelSelector } from './ModelSelector';
import { useChatSession } from '../hooks/useChatSession';
import { useWebSocket } from '../hooks/useWebSocket';

export const ChatInterface: React.FC = () => {
  const { session, messages, sendMessage, createSession, forkSession, deleteSession, sessions } = useChatSession();
  const { connect, disconnect, isConnected } = useWebSocket("/ws/chat");
  
  useEffect(() => {
    connect();
    return () => disconnect();
  }, [connect, disconnect]);
  
  const handleSend = async (content: string) => {
    await sendMessage(content);
  };
  
  return (
    <Flex className="h-screen bg-background" direction="row">
      <SessionSidebar
        sessions={sessions}
        currentSessionId={session?.id}
        onSelect={setCurrentSession}
        onCreate={createSession}
        onFork={forkSession}
        onDelete={deleteSession}
      />
      
      <Flex direction="column" className="flex-1 flex flex-col">
        {/* Header */}
        <Box className="border-b border-border px-4 py-3 flex items-center justify-between">
          <Heading level={2} size="lg" weight="semibold">
            {session?.title || "Nouvelle conversation"}
          </Heading>
          <ModelSelector onChange={setCheckpointId} />
        </Box>
        
        {/* Messages */}
        <Box className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((msg) => (
            msg.isStreaming ? (
              <TokenStream key={msg.id} initialContent={msg.content} />
            ) : (
              <MessageBubble key={msg.id} message={msg} />
            )
          ))}
        </Box>
        
        {/* Input */}
        <Box className="border-t border-border p-4">
          <ChatInput onSend={handleSend} disabled={!isConnected} />
        </Box>
      </Flex>
    </Flex>
  );
};
```

### `TokenStream.tsx` — Streaming Token par Token

```tsx
// web/src/features/chat/components/TokenStream.tsx
import { Box, Text } from '@/components/atoms';
import { useTokenStream } from '../hooks/useTokenStream';

interface TokenStreamProps {
  initialContent?: string;
  onComplete?: (fullContent: string) => void;
}

export const TokenStream: React.FC<TokenStreamProps> = ({ initialContent = "", onComplete }) => {
  const { content, isComplete, subscribe } = useTokenStream(initialContent);
  
  useEffect(() => {
    const unsubscribe = subscribe((token: string) => {
      // Appelé pour chaque token reçu via WS
    });
    return unsubscribe;
  }, [subscribe]);
  
  useEffect(() => {
    if (isComplete && onComplete) {
      onComplete(content);
    }
  }, [isComplete, content, onComplete]);
  
  return (
    <Box className="flex items-start gap-3">
      <Box className="w-8 h-8 rounded-full bg-primary flex items-center justify-center flex-shrink-0">
        <BotIcon className="w-5 h-5 text-primary-foreground" />
      </Box>
      <Box className="flex-1 min-w-0">
        <Text color="muted" size="sm" className="mb-1">Assistant</Text>
        <Box className="bg-card p-4 rounded-xl border border-border">
          <Text className="whitespace-pre-wrap font-mono text-sm">
            {content}
            {!isComplete && <span className="animate-pulse">▌</span>}
          </Text>
        </Box>
      </Box>
    </Box>
  );
};
```

### `useWebSocket.ts` — Hook WebSocket Robuste

```ts
// web/src/features/chat/hooks/useWebSocket.ts
import { useEffect, useRef, useState, useCallback } from 'react';

interface WSMessage {
  type: 'token' | 'start' | 'end' | 'error' | 'pong';
  content?: string;
  messageId?: string;
  usage?: any;
}

export function useWebSocket(url: string) {
  const wsRef = useRef<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WSMessage | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const messageHandlersRef = useRef<Set<(msg: WSMessage) => void>>(new Set());
  
  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;
    
    const ws = new WebSocket(url);
    wsRef.current = ws;
    
    ws.onopen = () => setIsConnected(true);
    ws.onclose = () => {
      setIsConnected(false);
      // Reconnect après 3s
      reconnectTimeoutRef.current = setTimeout(connect, 3000);
    };
    ws.onerror = () => ws.close();
    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data) as WSMessage;
        setLastMessage(msg);
        messageHandlersRef.current.forEach(handler => handler(msg));
      } catch {}
    };
  }, [url]);
  
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
    wsRef.current?.close();
    wsRef.current = null;
  }, []);
  
  const send = useCallback((data: any) => {
    wsRef.current?.send(JSON.stringify(data));
  }, []);
  
  const subscribe = useCallback((handler: (msg: WSMessage) => void) => {
    messageHandlersRef.current.add(handler);
    return () => messageHandlersRef.current.delete(handler);
  }, []);
  
  useEffect(() => {
    connect();
    return () => disconnect();
  }, [connect, disconnect]);
  
  return { connect, disconnect, send, subscribe, isConnected, lastMessage };
}
```

---

## 8. Critères d'Acceptation

| Critère | Seuil |
|---------|-------|
| Latence first token | < 2s (modèle chargé) |
| Streaming fluidité | 10-50 tokens/sec affichés |
| Compatibilité OpenAI | `/v1/chat/completions` passe tests officiels |
| WebSocket reconnexion | Auto-reconnect < 5s après coupure |
| Historique sessions | CRUD complet, fork, export |
| Frontend bundle | < 200KB gzippé (chat feature) |
| Accessibilité | ARIA labels, navigation clavier, focus visible |