USE clinica_vet;
-- Execute na base usada pela clínica. A instrução também pode ser reaplicada.
-- Se houver vacinas duplicadas no controle, reconcilie-as antes de aplicar a restrição.
SET @existe = (
    SELECT COUNT(*) FROM information_schema.statistics
    WHERE table_schema = DATABASE() AND table_name = 'integracao_governo'
      AND column_name = 'vacina_id' AND non_unique = 0
);
SET @sql = IF(@existe > 0, 'SELECT 1', 'ALTER TABLE integracao_governo ADD UNIQUE INDEX uq_integracao_vacina (vacina_id)');
PREPARE alterar FROM @sql;
EXECUTE alterar;
DEALLOCATE PREPARE alterar;
