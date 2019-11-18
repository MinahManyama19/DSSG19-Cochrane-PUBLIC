import sys

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from tqdm import tqdm

sys.path.append('../store/')


class RandomForestEm:

    """
    Random Forest classifer using Embeddings

    This ensemble RF classifer uses the defined features to initialize, train
    and then perform prediction.

    Parameters
    ==========

    fold_hash : str
        Unique identifier for the fold
    seed : int
        Seed for the RF
    n_estimators: int
        The number of trees to be trained
    max_depth: int
        The maximum number of branches to employ for each tree
    max_features: int or str
        The maximum number of features to consider at each split
    min_samples_split: int
        The minimum number of data points there must be per split
    min_samples_leaf: int
        The minimum number of samples there must be per leaf

    """

    def __init__(self, fold_hash, seed, n_estimators=10, max_depth=None,
                 max_features='auto', min_samples_leaf=1, n_jobs=-1):

        # identify which fold model was trained on
        self.fold_hash = fold_hash

        # hyperparameters
        self.seed = seed
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.max_features ='auto'
        self.min_samples_leaf = min_samples_leaf
        self.n_jobs = n_jobs

        # define empty dictionary to store models
        self.models = {}

    def train(self, x_train, y_train):

        """
        Trains one random forest per review group. Saves the trained
        classifiers within self.models.

        Parameters
        ==========

        x_train : pandas DataFrame
            DataFrame containing the papers we aim to
            classify, with ay least the column:
                average_embeddings - average word embeddings for concatenated title and abstract

        y_train : pandas DataFrame
            DataFrame containing the labels for each paper. Each
            column represents one review group with binary labels.
        """

        # convert input to format for classifier
        list_of_embeddings = list(x_train['average_embeddings'])
        x_train = np.array([[float(i) for i in embedding.strip('[]').split()] for embedding in list_of_embeddings])

        # discard fold ID column from labels
        review_groups = [col for col in y_train.columns if not col=='k']

        for review_group in tqdm(review_groups, desc='Train Review Groups'):

            # pull label column
            labels = y_train[review_group]

            # instantiate classifier object
            classifier = RandomForestClassifier(n_estimators=self.n_estimators,
            max_depth=self.max_depth, max_features=self.max_features,
            min_samples_leaf=self.min_samples_leaf,
            random_state=self.seed, n_jobs=self.n_jobs).fit(x_train, labels)

            # RF classifier
            self.models[review_group] = classifier

    def predict(self, x_test):

        """
        Generates predictions from the trained classifiers. Each binary
        classifier is applied once.

        Parameters
        ==========

        x_test : pd.DataFrame
            papers that we want to classify.

        Returns
        =======
        
        scores : pd.DataFrame
            Dataframe containing the predictions generated by each model.
            Each column corresponds to a review group and the values in
            that column are the probabilities that each paper belong to
            that review group.
        """

        # convert input to format for classifier
        list_of_embeddings = list(x_test['average_embeddings'])
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