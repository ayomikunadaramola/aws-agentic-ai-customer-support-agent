
"""Unit tests for the Amazon Bedrock Knowledge Base retrieval tool."""

from unittest.mock import MagicMock, patch

import pytest

import main


# ---------------------------------------------------------
# Helper: Invoke the actual Knowledge Base tool
# ---------------------------------------------------------

def invoke_knowledge_base(query, response, kb_id="TEST_KB_123"):
    """
    Execute the original Knowledge Base function with a mocked
    AWS retrieval response.
    """

    mock_runtime = MagicMock()
    mock_runtime.retrieve.return_value = response

    with (
        patch.object(main, "KB_ID", kb_id),
        patch.object(main, "_bedrock_runtime", mock_runtime),
    ):
        result = main.search_knowledge_base.__wrapped__(query)

        return result, mock_runtime

    # ---------------------------------------------------------
    # Test 1: Successful Knowledge Base retrieval
    # ---------------------------------------------------------


def test_successful_knowledge_base_retrieval():
    response = {
        "retrievalResults": [
            {
                "content": {
                    "text": "Platinum customers receive priority support."
                }
            }
        ]
    }

    result, mock_runtime = invoke_knowledge_base(
        query="What are the benefits of Platinum membership?",
        response=response,
    )

    assert result == (
        "Platinum customers receive priority support."
    )

    mock_runtime.retrieve.assert_called_once_with(
        knowledgeBaseId="TEST_KB_123",
        retrievalQuery={
            "text": "What are the benefits of Platinum membership?"
        },
    )

    # ---------------------------------------------------------
    # Test 2: Multiple retrieved text chunks
    # ---------------------------------------------------------


def test_multiple_retrieval_results():
    response = {
        "retrievalResults": [
            {
                "content": {
                    "text": "Gold members receive a 10% discount."
                }
            },
            {
                "content": {
                    "text": "Platinum members receive a 15% discount."
                }
            },
        ]
    }

    result, mock_runtime = invoke_knowledge_base(
        query="Compare Gold and Platinum membership.",
        response=response,
    )

    assert result == (
        "Gold members receive a 10% discount."
        "\n---\n"
        "Platinum members receive a 15% discount."
    )

    mock_runtime.retrieve.assert_called_once()

    # ---------------------------------------------------------
    # Test 3: No retrieval results
    # ---------------------------------------------------------


def test_empty_knowledge_base_results():
    response = {
        "retrievalResults": []
    }

    result, mock_runtime = invoke_knowledge_base(
        query="Find an unavailable product.",
        response=response,
    )

    assert result == (
        "No relevant information found in the knowledge base."
    )

    mock_runtime.retrieve.assert_called_once()

    # ---------------------------------------------------------
    # Test 4: Knowledge Base is not configured
    # ---------------------------------------------------------


@pytest.mark.parametrize(
    "kb_id",
    [
        "",
        None,
        "<kbid>",
    ],
)
def test_knowledge_base_not_configured(kb_id):
    mock_runtime = MagicMock()

    with (
        patch.object(main, "KB_ID", kb_id),
        patch.object(main, "_bedrock_runtime", mock_runtime),
    ):
        result = main.search_knowledge_base.__wrapped__(
            "What is the return policy?"
        )

        assert result == "Knowledge base not configured."

        mock_runtime.retrieve.assert_not_called()

        # ---------------------------------------------------------
        # Test 5: Missing retrievalResults field
        # ---------------------------------------------------------


def test_missing_retrieval_results_field():
    result, mock_runtime = invoke_knowledge_base(
        query="Find product information.",
        response={},
    )

    assert result == (
        "No relevant information found in the knowledge base."
    )

    mock_runtime.retrieve.assert_called_once()

    # ---------------------------------------------------------
    # Test 6: Empty text in retrieval results
    # ---------------------------------------------------------


def test_empty_retrieval_text():
    response = {
        "retrievalResults": [
            {
                "content": {
                    "text": ""
                }
            },
            {
                "content": {}
            },
        ]
    }

    result, mock_runtime = invoke_knowledge_base(
        query="Find warranty information.",
        response=response,
    )

    assert result == (
        "No relevant information found in the knowledge base."
    )

    mock_runtime.retrieve.assert_called_once()

    # ---------------------------------------------------------
    # Test 7: Mixed valid and empty retrieval results
    # ---------------------------------------------------------


def test_mixed_retrieval_results():
    response = {
        "retrievalResults": [
            {
                "content": {
                    "text": ""
                }
            },
            {
                "content": {
                    "text": "Orders can be tracked using an order ID."
                }
            },
            {
                "content": {}
            },
        ]
    }

    result, mock_runtime = invoke_knowledge_base(
        query="How do I track an order?",
        response=response,
    )

    assert result == (
        "Orders can be tracked using an order ID."
    )

    mock_runtime.retrieve.assert_called_once()

    # ---------------------------------------------------------
    # Test 8: AWS Knowledge Base retrieval error
    # ---------------------------------------------------------


def test_knowledge_base_retrieval_error():
    mock_runtime = MagicMock()

    mock_runtime.retrieve.side_effect = RuntimeError(
        "Simulated AWS retrieval failure"
    )

    with (
        patch.object(main, "KB_ID", "TEST_KB_123"),
        patch.object(main, "_bedrock_runtime", mock_runtime),
        patch.object(main, "logger") as mock_logger,
    ):
        result = main.search_knowledge_base.__wrapped__(
            "What is the return policy?"
        )

        assert result == (
            "Knowledge base search failed: "
            "Simulated AWS retrieval failure"
        )

        mock_runtime.retrieve.assert_called_once()

        mock_logger.exception.assert_called_once_with(
            "Knowledge base retrieval failed"
        )
