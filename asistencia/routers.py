class DatabaseRouter:
    """
    Router para controlar las operaciones de bases de datos
    """

    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'asistencia' and hasattr(model, '_meta') and model._meta.db_table in ['tabla1',
                                                                                                      'tabla2']:
            return 'sqlserver'
        return 'default'

    def db_for_write(self, model, **hints):
        # Las tablas existentes son de solo lectura
        if model._meta.app_label == 'asistencia' and hasattr(model, '_meta') and model._meta.db_table in ['tabla1',
                                                                                                      'tabla2']:
            return None  # No permitir escritura en tablas existentes
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        # Permitir relaciones entre objetos de diferentes bases de datos
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        # Solo migrar modelos nuevos a la base de datos default
        if db == 'default':
            return True
        return False  # No migrar a la base de datos sqlserver