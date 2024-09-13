import json
from typing import List

from api.src.config import AppConfig
from api.src.logger import logger
from api.src.models import Models


def get_result_row():
    with open('api/evaluate/results.jsonl', 'r') as result_file:
        for line in result_file:
            yield json.loads(line)


def generate_scores_from_metrics(ground_truth_and_prediction, total_ground_truth, total_prediction):
    # If both total prediction and total ground truth are 0, return 0 for all scores
    if total_prediction + total_ground_truth == 0:
        return 0, 0, 0

    precision = ground_truth_and_prediction / total_prediction
    recall = ground_truth_and_prediction / total_ground_truth

    # If precision and recall are 0, return 0 for F1 score
    if precision + recall == 0:
        return 0, 0, 0

    f1_score = (2 * precision * recall) / (precision + recall)
    return precision, recall, f1_score


def generate_scores_cwe(model_name):
    ground_truth_and_prediction = 0
    total_ground_truth = 0
    total_prediction = 0

    for row in get_result_row():
        if row['model'] != model_name:
            continue

        ground_truth = row['ground_truth']
        prediction = row['predictions']

        ground_truth_cwes = set([review['cwe'] for review in ground_truth])
        prediction_cwes = set([review['cwe'] for review in prediction])

        # find intersection of ground truth and prediction
        ground_truth_and_prediction += len(
            ground_truth_cwes.intersection(prediction_cwes))

        total_ground_truth += len(ground_truth_cwes)

        total_prediction += len(prediction_cwes)

    return generate_scores_from_metrics(ground_truth_and_prediction, total_ground_truth, total_prediction)


def generate_scores_cwe_and_line_number(model_name):
    ground_truth_and_prediction = 0
    total_ground_truth = 0
    total_prediction = 0

    for row in get_result_row():
        if row['model'] != model_name:
            continue

        ground_truth = row['ground_truth']
        prediction = row['predictions']

        ground_truth_cwes = set(
            [f"{review['cwe']}_{review['line_number']}" for review in ground_truth])
        prediction_cwes = set(
            [f"{review['cwe']}_{review['line_number']}" for review in prediction])

        # find intersection of ground truth and prediction
        ground_truth_and_prediction += len(
            ground_truth_cwes.intersection(prediction_cwes))

        total_ground_truth += len(ground_truth_cwes)

        total_prediction += len(prediction_cwes)

    return generate_scores_from_metrics(ground_truth_and_prediction, total_ground_truth, total_prediction)


if __name__ == '__main__':
    config = AppConfig.get_config()
    models: List[Models] = config.evaluate.get('models', [])
    model_names = [model.value for model in models]
    for model in model_names:
        precision, recall, f1_score = generate_scores_cwe(model)
        logger.info(
            f"Model: {model} Scores with CWE = Precision: {'{:.3f}'.format(precision)}, Recall: {'{:.3f}'.format(recall)}, F1 Score: {'{:.3f}'.format(f1_score)}")

        precision, recall, f1_score = generate_scores_cwe_and_line_number(
            model)
        logger.info(
            f"Model: {model} Scores with CWE and Line Number = Precision: {'{:.3f}'.format(precision)}, Recall: {'{:.3f}'.format(recall)}, F1 Score: {'{:.3f}'.format(f1_score)}")
