package xiaozhi.modules.mobile.dao;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import org.apache.ibatis.annotations.Mapper;
import xiaozhi.modules.mobile.entity.ParentProfile;

/**
 * Parent Profile DAO
 * Data access object for parent_profiles table
 */
@Mapper
public interface ParentProfileDao extends BaseMapper<ParentProfile> {
    
}