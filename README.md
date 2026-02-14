# siengeAPI – Automação e Integrações com o Sienge
Este repositório reúne um conjunto de automações e integrações desenvolvidas para comunicação com diversas APIs do Sienge.  
O projeto foi estruturado com foco em **organização, escalabilidade e facilidade de manutenção**, permitindo evoluções contínuas e seguras.

---

## 🚀 Objetivo do Projeto
Criar uma base sólida para automatizar processos relacionados ao Sienge, centralizando regras de negócio, padronizando integrações e facilitando a execução de rotinas críticas.

---

## 📂 Estrutura do Projeto
siengeAPI/
- ├── Dockerfile
- ├── compose.yml
- ├── requirements.txt
- ├── scripts/
- │   ├── api_*.py
- │   ├── db_utils.py
- │   ├── config.py
- │   ├── main.py
- │   └── ...
- └── .gitignore

---

### **Principais diretórios**
- **scripts/**  
  Contém todos os módulos de integração, utilitários, configurações e rotinas de execução.
- **Dockerfile / compose.yml**  
  Permitem execução padronizada em ambiente containerizado.
- **requirements.txt**  
  Lista de dependências necessárias para rodar o projeto.

---

## 🧩 Funcionalidades
- Integração com múltiplos endpoints do Sienge  
- Organização modular por domínio (clientes, unidades, contratos, contas, etc.)  
- Utilitários para banco de dados e logs  
- Execução automatizada de rotinas  
- Preparado para rodar em Docker  
- Estrutura limpa e fácil de expandir  

---

## 🛠️ Tecnologias Utilizadas
- **Python 3**
- **Requests**
- **Pandas**
- **Docker**
- **APIs REST**
- **Ambiente Linux**

---

## ▶️ Como Executar
```bash
### 1. Instalar dependências
pip install -r requirements.txt
### 2. Executar o script principal
python scripts/main.py
### 3. (Opcional) Executar via Docker
docker compose up --build
```
---

## 📌 Boas Práticas Adotadas
- `.gitignore` configurado para evitar arquivos desnecessários  
- Estrutura de pastas clara e modular  
- Commits padronizados e descritivos  
- Separação entre lógica, configuração e utilitários  
- Repositório limpo e sem arquivos temporários  

---

📈 Roadmap (Próximos Passos)
- [ ] Criar testes automatizados
- [ ] Adicionar logs estruturados
- [ ] Criar documentação das APIs
- [ ] Implementar CI/CD
- [ ] Criar releases versionadas

---

🤝 Contribuições
Contribuições são bem-vindas!
Sugestões, melhorias e correções podem ser enviadas via Issues ou Pull Requests.

---

📄 Licença
Este projeto é distribuído sob a licença MIT.
Sinta-se livre para usar, modificar e distribuir conforme necessário.
