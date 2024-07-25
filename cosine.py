import numpy as np
from scipy import spatial

class KNearestNeighbours:
    """" We calculate the cosine similarity in batches to prevent out of memory issues """

    def __init__(self, db, batch_size, metric="cosine"):
        self.db = db
        self.batch_size = batch_size

        distance_metrics = {
            "cosine": spatial.distance.cosine,
            "L1": spatial.distance.cityblock,
            "L2": spatial.distance.euclidean,
            "Linf": spatial.distance.chebyshev,
        }

        self.metric = distance_metrics[metric]

    def generator(self):
        query = "SELECT course_code, embedding FROM courses"
        return self.db.fetch_query_as_pandas(query, chunksize=self.batch_size)

    def fetch_k_closest(self, query, k):
        
        # Get closest courses per batch
        all = []
        cnt = 0
        for batch in self.generator():
            cnt += 1
            print("batch: ", cnt)
            all += self._fetch_closest_per_batch(batch, query, k)

        # Only keep course codes that are k closest to query
        return [x[0] for x in list(sorted(all, key=lambda x: x[1]))[:k]]

    def _fetch_closest_per_batch(self, batch, query, k):
        """ Return closest matches for batch 
        
        Returns: [course_code_1, distance_to_query_1], ... , [course_code_k, distance_to_query_k] ]
        Ordered in ascending order
        """
        # extract embeddings
        embeddings = np.stack([np.array(x.split(), dtype=float)  for x in batch["embedding"]]) # dimensions: [batch_size, 1536]

        # calculate distance from courses to query
        distances = []
        for course in embeddings:
            distances.append(self.metric(course, query))
        
        # get closest courses
        idxes = np.argsort(np.array(distances, dtype=float))[:k]
        return list(zip(
                list(batch.loc[idxes, "course_code"]),
                list(np.array(distances)[idxes])
            ))