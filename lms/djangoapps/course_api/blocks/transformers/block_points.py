"""
Block Points Transformer
"""


from lms.djangoapps.grades.api import CourseGradeFactory
from openedx.core.djangoapps.content.block_structure.transformer import BlockStructureTransformer


class BlockPointsTransformer(BlockStructureTransformer):
    """
    Keep points (grades) of chapter blocks
    """
    WRITE_VERSION = 1
    READ_VERSION = 1
    BLOCK_POINTS = 'block_points'

    @classmethod
    def name(cls):
        return "blocks_api:block_points"

    @classmethod
    def collect(cls, block_structure):
        """
        Collects any information that's necessary to execute this transformer's
        transform method.
        """
        # collect basic xblock fields
        block_structure.request_xblock_fields('category')

    def transform(self, usage_info, block_structure):
        """
        Mutates block_structure based on the given usage_info.
        """
        if usage_info.user and not usage_info.user.is_anonymous:
            try:
                chapter_points = CourseGradeFactory().read(
                    usage_info.user,
                    course_structure=block_structure,
                ).chapter_points
            except:
                chapter_points = {}

            for block_key in block_structure.topological_traversal():
                if block_structure.get_xblock_field(block_key, 'category') == 'chapter':
                    block_structure.set_transformer_block_field(
                        block_key,
                        self,
                        self.BLOCK_POINTS,
                        chapter_points.get(block_key, {'possible': 0, 'earned': 0})
                    )

