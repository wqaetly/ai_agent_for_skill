using System.Collections.Generic;
using UnityEngine;
using UnityEditor;
using NUnit.Framework;
using SkillSystem.Data;
using SkillSystem.Actions;

namespace SkillSystem.RAG.Tests
{
    /// <summary>
    /// 参数粒度增强功能单元测试
    /// 验证 REQ-02 的各项功能
    /// </summary>
    public class ParameterGranularityTests
    {
        private SkillData testSkillData;

        [SetUp]
        public void Setup()
        {
            // 创建测试用的技能数据
            testSkillData = new SkillData
            {
                skillName = "测试技能",
                skillDescription = "一个包含伤害和位移的测试技能",
                totalDuration = 60,
                frameRate = 30,
                tracks = new List<SkillTrack>
                {
                    new SkillTrack
                    {
                        trackName = "主轨道",
                        enabled = true,
                        actions = new List<ISkillAction>
                        {
                            new DamageAction
                            {
                                frame = 0,
                                duration = 10,
                                enabled = true,
                                baseDamage = 100f,
                                damageType = DamageType.Physical
                            },
                            new MovementAction
                            {
                                frame = 15,
                                duration = 20,
                                enabled = true,
                                movementType = MovementType.Linear,
                                movementSpeed = 500f
                            }
                        }
                    }
                }
            };
        }

        [Test]
        public void TestSkillContextAssembler_ExtractsBasicInfo()
        {
            // Arrange & Act
            var context = SkillContextAssembler.AssembleContext(testSkillData);

            // Assert
            Assert.IsNotNull(context);
            Assert.AreEqual("测试技能", context.skillName);
            Assert.AreEqual(60, context.totalDuration);
            Assert.AreEqual(30, context.frameRate);
            Assert.AreEqual(2f, context.durationInSeconds, 0.01f);
        }

        [Test]
        public void TestSkillContextAssembler_ExtractsActions()
        {
            // Arrange & Act
            var context = SkillContextAssembler.AssembleContext(testSkillData);

            // Assert
            Assert.AreEqual(2, context.existingActions.Count);
            Assert.AreEqual("DamageAction", context.existingActions[0].actionType);
            Assert.AreEqual("MovementAction", context.existingActions[1].actionType);
        }

        [Test]
        public void TestSkillContextAssembler_ExtractsTags()
        {
            // Arrange & Act
            var context = SkillContextAssembler.AssembleContext(testSkillData);

            // Assert
            Assert.IsTrue(context.tags.Contains("伤害"));
            Assert.IsTrue(context.tags.Contains("位移"));
        }

        [Test]
        public void TestParameterDependencyGraph_ValidatesConditionalRequired()
        {
            // Arrange
            var graph = new ActionParameterDependencyGraph();
            var parameters = new Dictionary<string, object>
            {
                { "movementType", "Arc" }
                // arcHeight 缺失
            };

            // Act
            var result = graph.ValidateParameters("MovementAction", parameters);

            // Assert
            Assert.IsFalse(result.isValid);
            Assert.IsTrue(result.issues.Exists(i => i.parameterName == "arcHeight"));
        }

        [Test]
        public void TestParameterDependencyGraph_ValidatesExclusive()
        {
            // Arrange
            var graph = new ActionParameterDependencyGraph();
            var parameters = new Dictionary<string, object>
            {
                { "damageType", "Physical" },
                { "spellVampPercentage", 0.2f }  // 物理伤害不应该有法术吸血
            };

            // Act
            var result = graph.ValidateParameters("DamageAction", parameters);

            // Assert
            Assert.IsFalse(result.isValid);
            Assert.IsTrue(result.issues.Exists(i =>
                i.parameterName == "spellVampPercentage" &&
                i.severity == IssueSeverity.Warning));
        }

        [Test]
        public void TestParameterDependencyGraph_ValidatesRange()
        {
            // Arrange
            var graph = new ActionParameterDependencyGraph();
            var parameters = new Dictionary<string, object>
            {
                { "baseDamage", 15000f }  // 超出推荐范围
            };

            // Act
            var result = graph.ValidateParameters("DamageAction", parameters);

            // Assert
            Assert.IsFalse(result.isValid);
            Assert.IsTrue(result.issues.Exists(i =>
                i.parameterName == "baseDamage" &&
                i.severity == IssueSeverity.Warning));
        }

        [Test]
        public void TestParameterInferencer_InfersParameters()
        {
            // Arrange
            var inferencer = new ParameterInferencer();
            var context = SkillContextAssembler.AssembleContext(testSkillData);

            // Act
            var result = inferencer.InferParameters("DamageAction", context);

            // Assert
            Assert.IsNotNull(result);
            Assert.Greater(result.parameterInferences.Count, 0);

            // 验证baseDamage参数被推断
            var baseDamageInference = result.parameterInferences.Find(p => p.parameterName == "baseDamage");
            Assert.IsNotNull(baseDamageInference);
            Assert.IsNotNull(baseDamageInference.recommendedValue);
        }

        [Test]
        public void TestParameterInferencer_CalculatesConfidence()
        {
            // Arrange
            var inferencer = new ParameterInferencer();
            var context = SkillContextAssembler.AssembleContext(testSkillData);

            // Act
            var result = inferencer.InferParameters("DamageAction", context);

            // Assert
            var baseDamageInference = result.parameterInferences.Find(p => p.parameterName == "baseDamage");
            Assert.IsNotNull(baseDamageInference);
            Assert.GreaterOrEqual(baseDamageInference.confidence, 0f);
            Assert.LessOrEqual(baseDamageInference.confidence, 1f);
        }

        [Test]
        public void TestParameterGranularityEnhancer_EnhancesRecommendation()
        {
            // Arrange
            var enhancer = ParameterGranularityEnhancer.Instance;
            var recommendation = new EnhancedActionRecommendation
            {
                action_type = "DamageAction",
                display_name = "伤害",
                category = "Combat",
                description = "造成伤害",
                semantic_similarity = 0.85f,
                final_score = 0.90f,
                reference_skills = new List<string> { "技能A", "技能B" }
            };

            // Act
            var enhanced = enhancer.EnhanceActionRecommendation(recommendation, testSkillData);

            // Assert
            Assert.IsNotNull(enhanced);
            Assert.AreEqual("DamageAction", enhanced.actionType);
            Assert.Greater(enhanced.parameterInferences.Count, 0);
            Assert.IsNotNull(enhanced.skillContext);
            Assert.IsNotNull(enhanced.recommendationSummary);
        }

        [Test]
        public void TestParameterGranularityEnhancer_GeneratesOdinOutput()
        {
            // Arrange
            var enhancer = ParameterGranularityEnhancer.Instance;
            var recommendation = new EnhancedActionRecommendation
            {
                action_type = "MovementAction",
                display_name = "位移",
                category = "Movement",
                semantic_similarity = 0.80f,
                final_score = 0.85f
            };

            // Act
            var enhanced = enhancer.EnhanceActionRecommendation(recommendation, testSkillData);

            // Assert
            Assert.IsNotNull(enhanced.odinFriendlyParameters);
            Assert.Greater(enhanced.odinFriendlyParameters.Count, 0);
        }

        [Test]
        public void TestParameterGranularityEnhancer_HealthCheck()
        {
            // Arrange
            var enhancer = ParameterGranularityEnhancer.Instance;

            // Act
            bool isHealthy = enhancer.HealthCheck(out string message);

            // Assert
            Assert.IsTrue(isHealthy);
            Assert.IsFalse(string.IsNullOrEmpty(message));
        }

        [Test]
        public void TestParameterStatisticsCache_ReturnsStatistics()
        {
            // Arrange
            var cache = new ParameterStatisticsCache();

            // Act
            var stats = cache.GetStatistics("DamageAction", "baseDamage");

            // Assert
            Assert.IsNotNull(stats);
            Assert.Greater(stats.sampleCount, 0);
            Assert.Greater(stats.median, 0);
        }

        [Test]
        public void TestSkillContextAssembler_InfersSkillIntents()
        {
            // Arrange & Act
            var context = SkillContextAssembler.AssembleContext(testSkillData);

            // Assert
            Assert.IsNotNull(context.inferredIntents);
            Assert.Greater(context.inferredIntents.Count, 0);
        }

        [Test]
        public void TestParameterInference_ProvidesAlternativeValues()
        {
            // Arrange
            var inferencer = new ParameterInferencer();
            var context = SkillContextAssembler.AssembleContext(testSkillData);

            // Act
            var result = inferencer.InferParameters("DamageAction", context);

            // Assert
            var baseDamageInference = result.parameterInferences.Find(p => p.parameterName == "baseDamage");
            Assert.IsNotNull(baseDamageInference);
            // 统计数据存在时应该有备选值
            if (baseDamageInference.confidence > 0.5f)
            {
                Assert.Greater(baseDamageInference.alternativeValues.Count, 0);
            }
        }
    }
}
