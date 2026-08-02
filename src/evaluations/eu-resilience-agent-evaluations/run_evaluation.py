from azure.ai.evaluation import GroundednessEvaluator, SimilarityEvaluator

def run_local_test(query, response, context, ground_truth):
    model_config = {
    "azure_endpoint": os.environ["AZURE_OPENAI_ENDPOINT"],
    "azure_deployment": MODEL_DEPLOYMENT,
    }
    groundedness = GroundednessEvaluator(model_config)
    similarity = SimilarityEvaluator(model_config)

    print(groundedness(
        query=query, response=response, context=context
    ))
    print(similarity(
        query=query, response=response, ground_truth=ground_truth
))


    # We have local evaluation(s)
