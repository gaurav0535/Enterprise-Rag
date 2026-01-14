import logging



"""
{
  "job_id": str | None,
  "doc_id": str | None,
  "component": str,   # app | pipeline | embedder | indexer | registry | retriever
  "action": str       # start | end | delete | embed | search | fail | skip
}


"""
LOG_FORMAT = (
    "%(asctime)s | %(levelname)s | %(name)s | %(message)s | %(job_id)s | %(doc_id)s | %(component)s | %(action)s"
)

class ContextFilter(logging.Filter):
    def filter(self, record):
        for field in ["job_id", "doc_id", "component", "action"]:
            if not hasattr(record, field):
                setattr(record, field, None)
        return True

def configure_logging():
    logging.basicConfig(
        level=logging.INFO,
        format=LOG_FORMAT,
    )
    logging.getLogger().addFilter(ContextFilter())





