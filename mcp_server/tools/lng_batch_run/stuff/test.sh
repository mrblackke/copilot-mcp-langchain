#!/bin/bash

####################################
### activate virtual environment ###
####################################
cd ../../../../
. ./.virtualenv/Scripts/activate

#####################
### lng_batch_run ###
#####################
# Testing all pipeline features with maximum coverage

echo "🚀 lng_batch_run pipeline testing - comprehensive coverage"
echo

# Basic tool execution
echo "📋 TEST 1: Basic tool execution"
python -m mcp_server.run run lng_batch_run '{\"pipeline\":[{\"tool\":\"lng_count_words\",\"params\":{\"input_text\":\"hello world\"},\"output\":\"stats\"}],\"final_result\":\"{! stats.wordCount !}\"}'
echo

# Variable substitution chain  
echo "📋 TEST 2: Variable substitution chain"
python -m mcp_server.run run lng_batch_run '{\"pipeline\":[{\"tool\":\"lng_count_words\",\"params\":{\"input_text\":\"count these words\"},\"output\":\"word_stats\"},{\"tool\":\"lng_math_calculator\",\"params\":{\"expression\":\"{! word_stats.wordCount !} * 10\"},\"output\":\"multiplied\"}],\"final_result\":\"{! multiplied.result !}\"}'
echo

# Conditional logic - true branch
echo "📋 TEST 3: Conditional logic - true branch"
python -m mcp_server.run run lng_batch_run '{\"pipeline\":[{\"tool\":\"lng_math_calculator\",\"params\":{\"expression\":\"10\"},\"output\":\"number\"},{\"type\":\"condition\",\"condition\":\"{! number.result > 5 !}\",\"then\":[{\"tool\":\"lng_count_words\",\"params\":{\"input_text\":\"true branch executed\"},\"output\":\"branch_result\"}],\"else\":[{\"tool\":\"lng_count_words\",\"params\":{\"input_text\":\"false branch executed\"},\"output\":\"branch_result\"}]}],\"final_result\":\"{! branch_result.wordCount !}\"}'
echo

# Conditional logic - false branch
echo "📋 TEST 4: Conditional logic - false branch"
python -m mcp_server.run run lng_batch_run '{\"pipeline\":[{\"tool\":\"lng_math_calculator\",\"params\":{\"expression\":\"2\"},\"output\":\"number\"},{\"type\":\"condition\",\"condition\":\"{! number.result > 5 !}\",\"then\":[{\"tool\":\"lng_count_words\",\"params\":{\"input_text\":\"true branch executed\"},\"output\":\"branch_result\"}],\"else\":[{\"tool\":\"lng_count_words\",\"params\":{\"input_text\":\"false branch executed\"},\"output\":\"branch_result\"}]}],\"final_result\":\"{! branch_result.wordCount !}\"}'
echo

# Parallel execution
echo "📋 TEST 5: Parallel execution"
python -m mcp_server.run run lng_batch_run '{\"pipeline\":[{\"type\":\"parallel\",\"parallel\":[{\"tool\":\"lng_count_words\",\"params\":{\"input_text\":\"first task\"},\"output\":\"task1\"},{\"tool\":\"lng_count_words\",\"params\":{\"input_text\":\"second task here\"},\"output\":\"task2\"},{\"tool\":\"lng_math_calculator\",\"params\":{\"expression\":\"5 + 5\"},\"output\":\"task3\"}]}],\"final_result\":\"{! task1.wordCount + task2.wordCount + task3.result !}\"}'
echo

# Delay functionality
echo "📋 TEST 6: Delay functionality (1 second delay)"
python -m mcp_server.run run lng_batch_run '{\"pipeline\":[{\"tool\":\"lng_count_words\",\"params\":{\"input_text\":\"before delay\"},\"output\":\"before\"},{\"type\":\"delay\",\"delay\":1.0},{\"tool\":\"lng_count_words\",\"params\":{\"input_text\":\"after delay\"},\"output\":\"after\"}],\"final_result\":\"{! before.wordCount + after.wordCount !}\"}'
echo

# Complex nested scenario
echo "📋 TEST 7: Complex nested scenario (condition + parallel)"
python -m mcp_server.run run lng_batch_run '{\"pipeline\":[{\"tool\":\"lng_count_words\",\"params\":{\"input_text\":\"This is a comprehensive test of nested execution\"},\"output\":\"initial\"},{\"type\":\"condition\",\"condition\":\"{! initial.wordCount > 5 !}\",\"then\":[{\"type\":\"parallel\",\"parallel\":[{\"tool\":\"lng_math_calculator\",\"params\":{\"expression\":\"{! initial.wordCount !} * 2\"},\"output\":\"calc1\"},{\"tool\":\"lng_math_calculator\",\"params\":{\"expression\":\"{! initial.wordCount !} + 10\"},\"output\":\"calc2\"}]}],\"else\":[{\"tool\":\"lng_math_calculator\",\"params\":{\"expression\":\"0\"},\"output\":\"calc1\"}]}],\"final_result\":\"{! calc1.result + (calc2.result || 0) !}\"}'
echo

# Mathematical expressions
echo "📋 TEST 8: Complex mathematical expressions"
python -m mcp_server.run run lng_batch_run '{\"pipeline\":[{\"tool\":\"lng_count_words\",\"params\":{\"input_text\":\"one two three four five\"},\"output\":\"words\"},{\"tool\":\"lng_math_calculator\",\"params\":{\"expression\":\"({! words.wordCount !} * 3) + ({! words.charactersWithSpaces !} / 2)\"},\"output\":\"complex_calc\"}],\"final_result\":\"{! complex_calc.result !}\"}'
echo

# String formatting in final_result
echo "📋 TEST 9: String formatting in final_result"
python -m mcp_server.run run lng_batch_run '{\"pipeline\":[{\"tool\":\"lng_count_words\",\"params\":{\"input_text\":\"test message\"},\"output\":\"stats\"}],\"final_result\":\"Words: {! stats.wordCount !}, Chars: {! stats.charactersWithSpaces !}\"}'
echo

# Nested conditions (if-then-else within if-then-else)
echo "📋 TEST 10: Nested conditions"
python -m mcp_server.run run lng_batch_run '{\"pipeline\":[{\"tool\":\"lng_math_calculator\",\"params\":{\"expression\":\"15\"},\"output\":\"num\"},{\"type\":\"condition\",\"condition\":\"{! num.result > 10 !}\",\"then\":[{\"type\":\"condition\",\"condition\":\"{! num.result > 20 !}\",\"then\":[{\"tool\":\"lng_count_words\",\"params\":{\"input_text\":\"very large number\"},\"output\":\"result\"}],\"else\":[{\"tool\":\"lng_count_words\",\"params\":{\"input_text\":\"medium number\"},\"output\":\"result\"}]}],\"else\":[{\"tool\":\"lng_count_words\",\"params\":{\"input_text\":\"small number\"},\"output\":\"result\"}]}],\"final_result\":\"{! result.wordCount !}\"}'
echo

# Multiple parallel groups
echo "📋 TEST 11: Multiple parallel groups"
python -m mcp_server.run run lng_batch_run '{\"pipeline\":[{\"type\":\"parallel\",\"parallel\":[{\"tool\":\"lng_count_words\",\"params\":{\"input_text\":\"first\"},\"output\":\"p1\"},{\"tool\":\"lng_count_words\",\"params\":{\"input_text\":\"second\"},\"output\":\"p2\"}]},{\"type\":\"parallel\",\"parallel\":[{\"tool\":\"lng_math_calculator\",\"params\":{\"expression\":\"{! p1.wordCount !} * 5\"},\"output\":\"m1\"},{\"tool\":\"lng_math_calculator\",\"params\":{\"expression\":\"{! p2.wordCount !} * 3\"},\"output\":\"m2\"}]}],\"final_result\":\"{! m1.result + m2.result !}\"}'
echo

# Variable access patterns
echo "📋 TEST 12: Variable access patterns"
python -m mcp_server.run run lng_batch_run '{\"pipeline\":[{\"tool\":\"lng_count_words\",\"params\":{\"input_text\":\"testing variable access patterns\"},\"output\":\"text_data\"}],\"final_result\":\"Count: {! text_data.wordCount !}, Length: {! text_data.charactersWithSpaces !}, NoSpaces: {! text_data.charactersWithoutSpaces !}\"}'
echo

# Conditional with parallel inside then and else
echo "📋 TEST 13: Conditional with parallel in both branches"
python -m mcp_server.run run lng_batch_run '{\"pipeline\":[{\"tool\":\"lng_math_calculator\",\"params\":{\"expression\":\"7\"},\"output\":\"check\"},{\"type\":\"condition\",\"condition\":\"{! check.result > 5 !}\",\"then\":[{\"type\":\"parallel\",\"parallel\":[{\"tool\":\"lng_count_words\",\"params\":{\"input_text\":\"true parallel one\"},\"output\":\"t1\"},{\"tool\":\"lng_count_words\",\"params\":{\"input_text\":\"true parallel two\"},\"output\":\"t2\"}]}],\"else\":[{\"type\":\"parallel\",\"parallel\":[{\"tool\":\"lng_count_words\",\"params\":{\"input_text\":\"false parallel one\"},\"output\":\"f1\"},{\"tool\":\"lng_count_words\",\"params\":{\"input_text\":\"false parallel two\"},\"output\":\"f2\"}]}]}],\"final_result\":\"{! (t1.wordCount || 0) + (t2.wordCount || 0) + (f1.wordCount || 0) + (f2.wordCount || 0) !}\"}'
echo

# Multiple delays
echo "📋 TEST 14: Multiple delays"
python -m mcp_server.run run lng_batch_run '{\"pipeline\":[{\"tool\":\"lng_count_words\",\"params\":{\"input_text\":\"step one\"},\"output\":\"s1\"},{\"type\":\"delay\",\"delay\":0.5},{\"tool\":\"lng_count_words\",\"params\":{\"input_text\":\"step two\"},\"output\":\"s2\"},{\"type\":\"delay\",\"delay\":0.3},{\"tool\":\"lng_count_words\",\"params\":{\"input_text\":\"step three\"},\"output\":\"s3\"}],\"final_result\":\"{! s1.wordCount + s2.wordCount + s3.wordCount !}\"}'
echo

# Long pipeline chain
echo "📋 TEST 15: Long pipeline chain"
python -m mcp_server.run run lng_batch_run '{\"pipeline\":[{\"tool\":\"lng_count_words\",\"params\":{\"input_text\":\"start\"},\"output\":\"step1\"},{\"tool\":\"lng_math_calculator\",\"params\":{\"expression\":\"{! step1.wordCount !} + 1\"},\"output\":\"step2\"},{\"tool\":\"lng_math_calculator\",\"params\":{\"expression\":\"{! step2.result !} * 2\"},\"output\":\"step3\"},{\"tool\":\"lng_math_calculator\",\"params\":{\"expression\":\"{! step3.result !} + 5\"},\"output\":\"step4\"},{\"tool\":\"lng_math_calculator\",\"params\":{\"expression\":\"{! step4.result !} / 2\"},\"output\":\"step5\"}],\"final_result\":\"{! step5.result !}\"}'
echo

# Error handling
echo "📋 TEST 16: Error handling (should fail gracefully)"
python -m mcp_server.run run lng_batch_run '{\"pipeline\":[{\"tool\":\"nonexistent_tool\",\"params\":{\"invalid\":\"parameter\"},\"output\":\"error_result\"}]}'
echo

# Empty pipeline
echo "📋 TEST 17: Empty pipeline"
python -m mcp_server.run run lng_batch_run '{\"pipeline\":[],\"final_result\":\"empty pipeline completed\"}'
echo

# Strategy architecture verification
echo "📋 TEST 18: Strategy architecture verification"
python -m mcp_server.run run lng_batch_run '{\"pipeline\":[{\"tool\":\"lng_count_words\",\"params\":{\"input_text\":\"strategy test\"},\"output\":\"strategy_test\"}]}'
echo

# Create test pipeline file for file-based tests
echo "📁 Creating test_pipeline.json for file-based testing..."
cat > mcp_server/tools/lng_batch_run/stuff/test_pipeline.json << 'EOF'
{
  \"pipeline\": [
    {
      \"tool\": \"lng_count_words\",
      \"params\": {\"input_text\": \"test pipeline from file\"},
      \"output\": \"stats\"
    }
  ],
  \"final_result\": \"Pipeline from file executed with {! stats.wordCount !} words\"
}
EOF
echo

# File-based pipeline tests
echo "📋 TEST 19: File-based pipeline execution"
python -m mcp_server.run run lng_batch_run '{\"pipeline_file\":\"mcp_server/tools/lng_batch_run/stuff/test_pipeline.json\"}'
echo

echo "📋 TEST 20: File-based pipeline with parameter override"
python -m mcp_server.run run lng_batch_run '{\"pipeline_file\":\"mcp_server/tools/lng_batch_run/stuff/test_pipeline.json\",\"final_result\":\"File pipeline result: {! stats.wordCount !}\"}'
echo

echo "📋 TEST 21: File-based telemetry pipeline"
python -m mcp_server.run run lng_batch_run '{\"pipeline_file\":\"mcp_server/tools/lng_batch_run/stuff/telemetry_pipeline.json\"}'
echo

# Clean up test files
echo "🧹 Cleaning up test files..."
rm -f mcp_server/tools/lng_batch_run/stuff/test_pipeline.json
echo "Test pipeline file removed."
echo

# NEW STRATEGY-BASED ARCHITECTURE TESTS
echo "🚀 NEW STRATEGY-BASED ARCHITECTURE TESTS"
echo

# forEach loop tests
echo "📋 TEST 22: forEach loop strategy"
python -m mcp_server.run run lng_batch_run '{\"pipeline\":[{\"tool\":\"lng_count_words\",\"params\":{\"input_text\":\"one two three\"},\"output\":\"words\"},{\"type\":\"forEach\",\"forEach\":\"{! [\\"apple\\", \\"banana\\", \\"cherry\\"] !}\",\"item\":\"fruit\",\"do\":[{\"tool\":\"lng_count_words\",\"params\":{\"input_text\":\"{! fruit !}\"},\"output\":\"count_{! fruit !}\"}]}],\"final_result\":\"{! count_apple.wordCount + count_banana.wordCount + count_cherry.wordCount !}\"}'
echo

# while loop tests  
echo "📋 TEST 23: while loop strategy"
python -m mcp_server.run run lng_batch_run '{\"pipeline\":[{\"tool\":\"lng_math_calculator\",\"params\":{\"expression\":\"0\"},\"output\":\"counter\"},{\"type\":\"while\",\"while\":\"{! counter.result < 3 !}\",\"do\":[{\"tool\":\"lng_math_calculator\",\"params\":{\"expression\":\"{! counter.result !} + 1\"},\"output\":\"counter\"}]}],\"final_result\":\"{! counter.result !}\"}'
echo

# repeat loop tests
echo "📋 TEST 24: repeat loop strategy" 
python -m mcp_server.run run lng_batch_run '{\"pipeline\":[{\"tool\":\"lng_math_calculator\",\"params\":{\"expression\":\"0\"},\"output\":\"sum\"},{\"type\":\"repeat\",\"repeat\":3,\"do\":[{\"tool\":\"lng_math_calculator\",\"params\":{\"expression\":\"{! sum.result !} + 5\"},\"output\":\"sum\"}]}],\"final_result\":\"{! sum.result !}\"}'
echo

# context_fields filtering tests
echo "📋 TEST 25: context_fields filtering (show specific fields)"
python -m mcp_server.run run lng_batch_run '{\"pipeline\":[{\"tool\":\"lng_count_words\",\"params\":{\"input_text\":\"test context filtering\"},\"output\":\"text_stats\"},{\"tool\":\"lng_math_calculator\",\"params\":{\"expression\":\"{! text_stats.wordCount !} * 2\"},\"output\":\"calc_result\"}],\"final_result\":\"{! calc_result.result !}\",\"context_fields\":[\"text_stats\"]}'
echo

echo "📋 TEST 26: context_fields filtering (show all)"
python -m mcp_server.run run lng_batch_run '{\"pipeline\":[{\"tool\":\"lng_count_words\",\"params\":{\"input_text\":\"test context all\"},\"output\":\"stats\"}],\"final_result\":\"{! stats.wordCount !}\",\"context_fields\":[\"*\"]}'
echo

echo "📋 TEST 27: context_fields filtering (hide all - default)"
python -m mcp_server.run run lng_batch_run '{\"pipeline\":[{\"tool\":\"lng_count_words\",\"params\":{\"input_text\":\"test context hidden\"},\"output\":\"hidden_stats\"}],\"final_result\":\"{! hidden_stats.wordCount !}\"}'
echo

# output_log tests
echo "📋 TEST 28: output_log functionality"
python -m mcp_server.run run lng_batch_run '{\"pipeline\":[{\"tool\":\"lng_count_words\",\"params\":{\"input_text\":\"test logging output\"},\"output\":\"log_test\",\"output_log\":\"test_output_data\"}],\"final_result\":\"{! log_test.wordCount !}\"}'
echo

# Python expressions tests
# Python expressions tests
echo "📋 TEST 29: Python expressions [! !] syntax"
python -m mcp_server.run run lng_batch_run '{\"pipeline\":[{\"tool\":\"lng_count_words\",\"params\":{\"input_text\":\"Python expressions test\"},\"output\":\"py_stats\"}],\"final_result\":\"[! py_stats.wordCount * 3 + len(\\"extra\\") !]\"}'
echo

# maxConcurrent in parallel strategy
echo "📋 TEST 30: maxConcurrent in parallel strategy"
python -m mcp_server.run run lng_batch_run '{\"pipeline\":[{\"type\":\"parallel\",\"maxConcurrent\":2,\"parallel\":[{\"tool\":\"lng_count_words\",\"params\":{\"input_text\":\"task 1\"},\"output\":\"t1\"},{\"tool\":\"lng_count_words\",\"params\":{\"input_text\":\"task 2\"},\"output\":\"t2\"},{\"tool\":\"lng_count_words\",\"params\":{\"input_text\":\"task 3\"},\"output\":\"t3\"},{\"tool\":\"lng_count_words\",\"params\":{\"input_text\":\"task 4\"},\"output\":\"t4\"}]}],\"final_result\":\"{! t1.wordCount + t2.wordCount + t3.wordCount + t4.wordCount !}\"}'
echo

# Architecture verification tests
echo "📋 TEST 31: Strategy architecture information"
python -m mcp_server.run run lng_batch_run '{\"pipeline\":[{\"tool\":\"lng_count_words\",\"params\":{\"input_text\":\"architecture test\"},\"output\":\"arch_test\"}],\"final_result\":\"Strategy system working\"}'
echo

# Mixed expressions tests
echo "📋 TEST 32: Mixed JavaScript and Python expressions"
python -m mcp_server.run run lng_batch_run '{\"pipeline\":[{\"tool\":\"lng_count_words\",\"params\":{\"input_text\":\"mixed expressions test\"},\"output\":\"mixed\"}],\"final_result\":\"JS: {! mixed.wordCount !}, Python: [! mixed.wordCount * 2 !]\"}'
echo

# Advanced loop with conditions
echo "📋 TEST 33: Advanced forEach with conditions"
python -m mcp_server.run run lng_batch_run '{\"pipeline\":[{\"type\":\"forEach\",\"forEach\":\"{! [1, 2, 3, 4, 5] !}\",\"item\":\"num\",\"do\":[{\"type\":\"condition\",\"condition\":\"{! num > 3 !}\",\"then\":[{\"tool\":\"lng_math_calculator\",\"params\":{\"expression\":\"{! num !} * 10\"},\"output\":\"result_{! num !}\"}],\"else\":[{\"tool\":\"lng_math_calculator\",\"params\":{\"expression\":\"{! num !}\"},\"output\":\"result_{! num !}\"}]}]}],\"final_result\":\"{! (result_4 ? result_4.result : 0) + (result_5 ? result_5.result : 0) !}\"}'
echo

# Variable delay tests
echo "📋 TEST 34: Variable delay with expression"
python -m mcp_server.run run lng_batch_run '{\"pipeline\":[{\"tool\":\"lng_math_calculator\",\"params\":{\"expression\":\"0.5\"},\"output\":\"delay_time\"},{\"type\":\"delay\",\"delay\":\"{! delay_time.result !}\"},{\"tool\":\"lng_count_words\",\"params\":{\"input_text\":\"after variable delay\"},\"output\":\"delayed\"}],\"final_result\":\"{! delayed.wordCount !}\"}'
echo

# Error handling in strategies
echo "📋 TEST 35: Error handling in forEach strategy"
python -m mcp_server.run run lng_batch_run '{\"pipeline\":[{\"type\":\"forEach\",\"forEach\":\"{! [\\"valid\\", \\"data\\"] !}\",\"item\":\"item\",\"do\":[{\"tool\":\"nonexistent_tool\",\"params\":{\"text\":\"{! item !}\"},\"output\":\"error_{! item !}\"}]}],\"final_result\":\"Should fail gracefully\"}'
echo

echo "🎉 lng_batch_run testing completed!"
echo "All major pipeline features have been tested for maximum coverage."
echo "✨ New strategy-based architecture fully tested with advanced features!"
