from django.db.models.signals import m2m_changed

logger = logging.getLogger("paperless.handlers")

def tags_changed(sender, instance, action, reverse, model, pk_set, **kwargs):
    """
    Fonction de rappel qui sera appelée lorsque le signal m2m_changed est reçu.
    """
    if action == 'post_add' or action == 'post_remove':
        # Appelez votre méthode ici
        pass