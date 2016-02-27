import numpy
from sklearn import svm
from sklearn.externals import joblib


def get_formatted_X(messages, features, use_tfidf=False):
    feature_num = len(features)
    message_num = len(messages)

    X = numpy.zeros((message_num, feature_num), dtype=numpy.float64)

    for idx, msg in enumerate(messages):
        for feature in features:
            X[idx, feature.feature_index] = feature.tfidf if use_tfidf else feature.count


    return X

def get_formatted_y(source, messages):

    code_num = 0
    code_map = {}
    code_map_inverse = {}

    y = []
    for idx, msg in enumerate(messages):
        code_id = msg.code_assignments.get(source=source, valid=True, is_user_labeled=True).code.id
        code_index = code_map.get(code_id)
        if code_index is None:
            code_index = code_num
            code_map[code_id] = code_index
            code_map_inverse[code_index] = code_id
            code_num += 1

        y.append(code_index)

    return y, code_map_inverse

def get_formatted_data(source, messages, features, use_tfidf=False):
    X = get_formatted_X(messages, features)
    y, code_map_inverse = get_formatted_y(source, messages)

    return X, y, code_map_inverse


def train_model(X, y, model_save_path=None):
    lin_clf = svm.LinearSVC()
    lin_clf.fit(X, y)

    if model_save_path:
        joblib.dump(lin_clf, model_save_path + "/model.pkl")

    return lin_clf


def get_prediction(lin_model, X):
    prediction = lin_model.predict(X)

    if hasattr(lin_model, "predict_proba"):
        prob = lin_model.predict_proba(X)[:, 1]
    else:  # use decision function
        prob = lin_model.decision_function(X)
        min = prob.min()
        max = prob.max()
        prob = \
            (prob - min) / (max - min)

    return prediction, prob