DROP DATABASE clinica_vet;
CREATE DATABASE IF NOT EXISTS clinica_vet;
USE clinica_vet;
-- 1. Endereço
CREATE TABLE IF NOT EXISTS endereco (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    cep VARCHAR(8) NOT NULL,
    logradouro VARCHAR(160),
    numero VARCHAR(20),
    complemento VARCHAR(120),
    bairro VARCHAR(120),
    cidade VARCHAR(120),
    uf VARCHAR(2),
    codigo_ibge VARCHAR(7)
);
-- 2. Tutor
CREATE TABLE IF NOT EXISTS tutor (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    nome_completo VARCHAR(150) NOT NULL,
    cpf VARCHAR(11) UNIQUE NOT NULL,
    data_nascimento DATE,
    email VARCHAR(254) NOT NULL,
    telefone VARCHAR(20),
    endereco_id BIGINT,
    cadastrado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    situacao VARCHAR(10) DEFAULT 'ATIVO',
    FOREIGN KEY (endereco_id) REFERENCES endereco(id) ON DELETE SET NULL
);
-- 3. Espécie
CREATE TABLE IF NOT EXISTS especie (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(80) NOT NULL,
    descricao TEXT,
    situacao VARCHAR(10) DEFAULT 'ATIVA'
);
-- 4. Raça
CREATE TABLE IF NOT EXISTS raca (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    especie_id BIGINT NOT NULL,
    nome VARCHAR(80) NOT NULL,
    descricao TEXT,
    situacao VARCHAR(10) DEFAULT 'ATIVA',
    FOREIGN KEY (especie_id) REFERENCES especie(id) ON DELETE CASCADE
);
-- 5. Veterinário
CREATE TABLE IF NOT EXISTS veterinario (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    nome_completo VARCHAR(150) NOT NULL,
    cpf VARCHAR(11) UNIQUE NOT NULL,
    numero_crmv VARCHAR(20) NOT NULL,
    uf_crmv VARCHAR(2) NOT NULL,
    email VARCHAR(254) UNIQUE NOT NULL,
    telefone VARCHAR(20),
    senha_hash TEXT NOT NULL,
    senha_confirmada BOOLEAN DEFAULT FALSE,
    cadastrado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    situacao VARCHAR(10) DEFAULT 'ATIVO',
    ultimo_acesso_em TIMESTAMP NULL
);
-- 6. Animal
CREATE TABLE IF NOT EXISTS animal (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    data_nascimento DATE,
    idade_estimada_meses INT,
    sexo VARCHAR(20),
    cor VARCHAR(80),
    peso_atual_kg DECIMAL(8,3),
    tutor_id BIGINT NOT NULL,
    especie_id BIGINT NOT NULL,
    raca_id BIGINT,
    situacao VARCHAR(20) DEFAULT 'ATIVO',
    FOREIGN KEY (tutor_id) REFERENCES tutor(id) ON DELETE CASCADE,
    FOREIGN KEY (especie_id) REFERENCES especie(id),
    FOREIGN KEY (raca_id) REFERENCES raca(id) ON DELETE SET NULL
);
-- 7. Vínculo Microchip
CREATE TABLE IF NOT EXISTS vinculo_microchip (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    animal_id BIGINT NOT NULL,
    veterinario_id BIGINT NOT NULL,
codigo_rfid VARCHAR(48) UNIQUE NOT NULL,
    vinculado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    encerrado_em TIMESTAMP NULL,
    FOREIGN KEY (animal_id) REFERENCES animal(id) ON DELETE CASCADE,
    FOREIGN KEY (veterinario_id) REFERENCES veterinario(id)
);
-- 8. Consulta
CREATE TABLE IF NOT EXISTS consulta (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    animal_id BIGINT NOT NULL,
    veterinario_id BIGINT NOT NULL,
    data_hora TIMESTAMP NOT NULL,
    motivo TEXT,
    anamnese TEXT,
    prescricao_medicamentos TEXT,
    peso_registrado_kg DECIMAL(8,3),
    temperatura_c DECIMAL(5,2),
    situacao VARCHAR(20) DEFAULT 'AGENDADA',
    FOREIGN KEY (animal_id) REFERENCES animal(id) ON DELETE CASCADE,
    FOREIGN KEY (veterinario_id) REFERENCES veterinario(id)
);
-- 9. Aplicação de Vacina
CREATE TABLE IF NOT EXISTS vacina (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    animal_id BIGINT NOT NULL,
    veterinario_id BIGINT NOT NULL,
    nome_vacina VARCHAR(120) NOT NULL,
    tipo_vacina VARCHAR(60),
    antirrabica BOOLEAN DEFAULT FALSE,
    fabricante_numero_lote VARCHAR(120),
    data_agendada DATE,
    data_aplicacao DATE,
    dose_etapa VARCHAR(60),
    proxima_dose_em DATE,
    situacao VARCHAR(10) DEFAULT 'APLICADA',
    FOREIGN KEY (animal_id) REFERENCES animal(id) ON DELETE CASCADE,
    FOREIGN KEY (veterinario_id) REFERENCES veterinario(id)
);
-- 10. Integração com o Governo
CREATE TABLE IF NOT EXISTS integracao_governo (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    animal_id BIGINT NOT NULL,
    vacina_id BIGINT,
    tipo_operacao VARCHAR(25) NOT NULL,
    chave_idempotencia VARCHAR(64) UNIQUE NOT NULL,
    protocolo_externo VARCHAR(100),
    situacao VARCHAR(12) DEFAULT 'PENDENTE',
    solicitada_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    respondida_em TIMESTAMP NULL,
    quantidade_tentativas INT DEFAULT 0,
    mensagem_erro TEXT,
    payload_envio JSON,
    FOREIGN KEY (animal_id) REFERENCES animal(id) ON DELETE CASCADE,
    FOREIGN KEY (vacina_id) REFERENCES vacina(id) ON DELETE SET NULL
);