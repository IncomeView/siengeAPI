<br>

## siengeAPI – Automação e Integrações com o Sienge
Arquitetura de dados, automação financeira e integrações corporativas
Este repositório reúne um conjunto de automações e integrações desenvolvidas para comunicação com diversas APIs do Sienge, com foco em operações financeiras, governança e performance corporativa.
A solução foi projetada para ambientes empresariais que exigem confiabilidade, rastreabilidade e escalabilidade em rotinas críticas.

<br><br>
## 🏢 Contexto Empresarial
Este projeto foi originalmente desenvolvido em um ambiente corporativo com operações financeiras complexas, envolvendo:
- múltiplas empresas ativas (+40)
- integrações entre ERP, CRM, cobrança e vendas
- necessidade de governança e consistência de dados
- rotinas críticas de FP&A, inadimplência, performance e controladoria
- consolidação de informações para áreas executivas
A automação via Sienge API surgiu para:
- padronizar integrações
- reduzir erros manuais
- garantir integridade dos dados
- acelerar análises financeiras
- estruturar pipelines escaláveis em PostgreSQL
- suportar decisões estratégicas em tempo real

<br><br>
## 🚀 Objetivo do Projeto
Criar uma base sólida para automatizar processos relacionados ao Sienge, centralizando regras de negócio, padronizando integrações e facilitando a execução de rotinas financeiras e operacionais.

<br><br>
## 📂 Estrutura do Projeto
```
siengeAPI/
├── Dockerfile
├── compose.yml
├── requirements.txt
├── scripts/
│   ├── api_*.py
│   ├── db_utils.py
│   ├── config.py
│   ├── main.py
│   └── ...
└── .gitignore
```

### **Principais diretórios**
- **scripts/**  
  Módulos de integração, utilitários, configurações e rotinas de execução.
- **Dockerfile / compose.yml**  
  Execução padronizada em ambiente containerizado.
- **requirements.txt**  
  Dependências de projeto.

<br><br>
## 🧩 Funcionalidades
- Integração com múltiplos endpoints do Sienge  
- Organização modular por domínio (clientes, unidades, contratos, contas, etc.)
- Utilitários para banco de dados, logs e autenticação
- Execução automatizada de rotinas financeiras
- Preparado para rodar em Docker
- Estrutura limpa, escalável e fácil de expandir
- Base ideal para pipelines corporativos de dados

<br><br>
## 🛠️ Tecnologias Utilizadas
- **Python 3**
- **Requests**
- **Pandas**
- **Docker**
- **APIs REST**
- **Ambiente Linux**
- **PostgreSQL (no ambiente corporativo original)**

<br><br>
## ▶️ Como Executar
```bash
### 1. Instalar dependências
pip install -r requirements.txt
### 2. Executar o script principal
python scripts/main.py
### 3. (Opcional) Executar via Docker
docker compose up --build
```

<br><br>
## 📌 Boas Práticas Adotadas
- `.gitignore` configurado para evitar arquivos desnecessários  
- Estrutura de pastas clara e modular
- Separação clara entre lógica, configuração e utilitários
- Commits padronizados e descritivos
- Preparado para CI/CD
- Repositório limpo e sem arquivos temporários

<br><br>
## 📈 Roadmap (Próximos Passos)
- [ ] Criar testes automatizados
- [ ] Adicionar logs estruturados para auditoria
- [ ] Criar documentação técnica das integrações
- [ ] Implementar CI/CD
- [ ] Criar releases versionadas
- [ ] Adicionar monitoramento e alertas
- [ ] Criar exemplos de uso para diferentes domínios (contratos, unidades, clientes etc.)

<br><br>
## 🤝 Contribuições
Contribuições são bem-vindas!
Sugestões, melhorias e correções podem ser enviadas via Issues ou Pull Requests.

<br><br>
## 📄 Licença
Este projeto é distribuído sob a licença MIT.
Sinta-se livre para usar, modificar e distribuir conforme necessário.

<br><br>
## 👤 Autor
Moacir Magalhães Faria  
IncomeView — Data & Financial Engineering
LinkedIn: www.linkedin.com/in/moacirfaria  
GitHub: https://github.com/MmsFaria

<br><br>

