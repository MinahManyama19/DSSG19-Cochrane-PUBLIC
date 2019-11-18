import pandas as pd
import numpy as np
from sklearn.linear_model import SGDClassifier
from collections import defaultdict
import sys
from tqdm import tqdm

sys.path.append('../store/')


class ElasticClassifierEm:

    """
    Elastic net classifer with embeddings as features

    One-vs-all logistic regression. The class contains one model for each review
    group, and returns the probability that an paper belongs to each of the
    review groups.

    Parameters
    ==========

    alpha : float
        Constant that is used in the regularization (l2). Defaults to 0.0001.

    l1_ratio : float
        Constant that is used int he regularization (l1). Defaults to 0.0001.

    embeddings_col : string
        Defines what column the embeddings live in.

    env : dict
        Dict containing filepaths.
        
    load_fresh : bool
        Whether persisted files should be used (False) or not (True).
    """

    def __init__(self, alpha=0.0001, l1_ratio=0.15, embeddings_col="average_embeddings",
                    env=None, load_fresh=False):

        # model contents
        self.models = defaultdict(dict)

        # parameter for logistic regression with elastic net
        self.alpha = alpha
        self.l1_ratio = l1_ratio

        self.embeddings_col = embeddings_col

        self.env = env
        self.load_fresh = load_fresh

    def train(self, x_train, y_train):

        """
        Trains one elastic logistic classifier per review group. Saves the trained
        classifiers within self.models.

        Parameters
        ==========

        x_train : pandas DataFrame
            DataFrame containing the papers we aim to
            classify, with at least the column:
                average_embeddings - average word embeddings for concatenated title and abstract

        y_train : pandas DataFrame
            DataFrame containing the labels for each paper. Each
            column represents one review group with binary labels.
        """

        # convert input to format for classifier
        list_of_embeddings = list(x_train[self.embeddings_col])
        x_train = np.array([[float(i) for i in embedding.strip('[]').split()] for embedding in list_of_embeddings])

        # discard fold ID column from labels
        review_groups = [col for col in y_train.columns if not col=='k']

        for review_group in tqdm(review_groups, desc='Train Review Groups'):

            # pull label column
            labels = y_train[review_group]

            # logistic classifier
            classifier = SGDClassifier(loss="log", alpha=self.alpha,
                        l1_ratio = self.l1_ratio, penalty="elasticnet").fit(x_train, labels)

            # save the model in dictionary of models
            self.models[review_group] = classifier

    def predict(self, x_test):

        """
        Generates predictions from the trained classifiers. Each binary
        classifier is applied once.

        Parameters
        ==========
        x_test : pd.DataFrame
            papers that we want to classify with at least the column:
                average_embeddings - average word embeddings for
                                     concatenated title and abstract

        Returns
        =======
        scores : pd.DataFrame
            Dataframe containing the predictions generated by each model.
            Each column corresponds to a review group and the values in
            that column are the probabilities that each paper belong to
            that review group.
        """

        # convert input to format for classifier
        list_of_embeddings = list(x_test[self.embeddings_col])
        x_test = np.array([[float(i) for i in embedding.strip('[]').split()] for embedding in list_of_embeddings])

        scores = {}

        for model_group in tqdm(self.models, desc='Test Review Groups'):

            # get the classifier
            classifier = self.models[model_group]

            # predictions as probabilities
            y_preds = classifier.predict_proba(x_test)

            probabilities = y_preds[:,1]

            # store scores of model
            scores[model_group] = probabilities

        scores = pd.DataFrame.from_dict(scores)

        return scores